#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>  // For NumPy support
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>  // For color conversions
#include <stdexcept>  // For error handling

#ifdef HAVE_FFMPEG
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libswscale/swscale.h>
#endif

namespace py = pybind11;

// A thin abstraction: when FFmpeg is available (HAVE_FFMPEG), use it to decode
// RTSP frames (with the possibility to extend to rkmpp/RGA). Otherwise, fall
// back to OpenCV VideoCapture for simplicity.

#ifdef HAVE_FFMPEG
// Minimal FFmpeg-based reader. This is a conservative, portable implementation
// that decodes packets into AVFrame and converts to BGR8 cv::Mat using sws.
class RTSPReader {
public:
    RTSPReader(const std::string& url) : fmt_ctx(nullptr), codec_ctx(nullptr), sws_ctx(nullptr), video_stream_index(-1) {
        avformat_network_init();
        if (avformat_open_input(&fmt_ctx, url.c_str(), nullptr, nullptr) != 0) {
            throw std::runtime_error("Failed to open RTSP stream: " + url);
        }
        if (avformat_find_stream_info(fmt_ctx, nullptr) < 0) {
            cleanup();
            throw std::runtime_error("Failed to find stream info");
        }

        for (unsigned i = 0; i < fmt_ctx->nb_streams; ++i) {
            if (fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
                video_stream_index = i;
                break;
            }
        }
        if (video_stream_index < 0) {
            cleanup();
            throw std::runtime_error("No video stream found");
        }

        AVCodecParameters* codecpar = fmt_ctx->streams[video_stream_index]->codecpar;
        const AVCodec* codec = avcodec_find_decoder(codecpar->codec_id);
        if (!codec) {
            cleanup();
            throw std::runtime_error("Unsupported codec");
        }

        codec_ctx = avcodec_alloc_context3(codec);
        if (!codec_ctx) {
            cleanup();
            throw std::runtime_error("Failed to allocate codec context");
        }
        if (avcodec_parameters_to_context(codec_ctx, codecpar) < 0) {
            cleanup();
            throw std::runtime_error("Failed to copy codec parameters");
        }

        if (avcodec_open2(codec_ctx, codec, nullptr) < 0) {
            cleanup();
            throw std::runtime_error("Failed to open codec");
        }

        pkt = av_packet_alloc();
        frame = av_frame_alloc();
    }

    ~RTSPReader() {
        cleanup();
    }

    cv::Mat read() {
        int ret = 0;
        while ((ret = av_read_frame(fmt_ctx, pkt)) >= 0) {
            if (pkt->stream_index == video_stream_index) {
                ret = avcodec_send_packet(codec_ctx, pkt);
                if (ret < 0) {
                    av_packet_unref(pkt);
                    continue;
                }
                ret = avcodec_receive_frame(codec_ctx, frame);
                av_packet_unref(pkt);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                    continue;
                } else if (ret < 0) {
                    throw std::runtime_error("Error decoding frame");
                }

                // Convert AVFrame to BGR cv::Mat
                int width = frame->width;
                int height = frame->height;
                int src_format = frame->format;
                // Setup sws context for conversion to BGR24
                SwsContext* local_sws = sws_getContext(width, height, (AVPixelFormat)src_format,
                                                      width, height, AV_PIX_FMT_BGR24,
                                                      SWS_BILINEAR, nullptr, nullptr, nullptr);
                if (!local_sws) {
                    throw std::runtime_error("Failed to create sws context");
                }

                cv::Mat out_mat(height, width, CV_8UC3);
                uint8_t* dest[4] = { out_mat.data, nullptr, nullptr, nullptr };
                int dest_linesize[4] = { static_cast<int>(out_mat.step[0]), 0, 0, 0 };

                sws_scale(local_sws, frame->data, frame->linesize, 0, height, dest, dest_linesize);
                sws_freeContext(local_sws);

                return out_mat;
            }
            av_packet_unref(pkt);
        }
        // If we exit loop, stream ended or error
        throw std::runtime_error("Failed to read frame from RTSP stream (EOF or error)");
    }

    void release() {
        // Nothing special: destructor frees resources
    }

private:
    AVFormatContext* fmt_ctx;
    AVCodecContext* codec_ctx;
    AVPacket* pkt;
    AVFrame* frame;
    SwsContext* sws_ctx;
    int video_stream_index;

    void cleanup() {
        if (pkt) { av_packet_free(&pkt); pkt = nullptr; }
        if (frame) { av_frame_free(&frame); frame = nullptr; }
        if (codec_ctx) { avcodec_free_context(&codec_ctx); codec_ctx = nullptr; }
        if (fmt_ctx) { avformat_close_input(&fmt_ctx); fmt_ctx = nullptr; }
        avformat_network_deinit();
    }
};
#else
// Fallback to OpenCV's VideoCapture
#include <opencv2/videoio.hpp>
class RTSPReader {
public:
    RTSPReader(const std::string& url) {
        if (!cap.open(url)) {
            throw std::runtime_error("Failed to open RTSP stream: " + url);
        }
    }

    cv::Mat read() {
        cv::Mat frame;
        if (!cap.read(frame)) {
            throw std::runtime_error("Failed to read frame from RTSP stream");
        }
        if (frame.empty()) {
            throw std::runtime_error("Received empty frame");
        }
        if (frame.type() != CV_8UC3 && frame.type() != CV_8UC1) {
            // Convert to 3-channel BGR for consistency
            cv::Mat conv;
            frame.convertTo(conv, CV_8U);
            if (conv.channels() == 1) cv::cvtColor(conv, conv, cv::COLOR_GRAY2BGR);
            return conv;
        }
        return frame;
    }

    void release() {
        cap.release();
    }

private:
    cv::VideoCapture cap;
};
#endif

// Expose to Python
PYBIND11_MODULE(rtsp_module, m) {
    py::class_<RTSPReader>(m, "RTSPReader")
        .def(py::init<const std::string&>())
        .def("read", &RTSPReader::read)
        .def("release", &RTSPReader::release);

    // Expose cv::Mat with buffer protocol for direct NumPy conversion
    py::class_<cv::Mat>(m, "Mat", py::buffer_protocol())
        .def_buffer([](cv::Mat& mat) -> py::buffer_info {
            if (mat.empty()) {
                throw std::runtime_error("Cannot expose empty Mat");
            }

            int channels = mat.channels();
            int rows = mat.rows;
            int cols = mat.cols;
            size_t elem_size = mat.elemSize1(); // size of one channel element

            // Determine format descriptor
            std::string format;
            if (elem_size == 1) {
                format = py::format_descriptor<uint8_t>::format();
            } else if (elem_size == 2) {
                format = py::format_descriptor<uint16_t>::format();
            } else {
                format = py::format_descriptor<uint8_t>::format();
            }

            // shape and strides
            std::vector<ssize_t> shape;
            std::vector<ssize_t> strides;
            if (channels == 1) {
                shape = { rows, cols };
                strides = { static_cast<ssize_t>(mat.step[0]), static_cast<ssize_t>(elem_size) };
                return py::buffer_info(mat.data, elem_size, format, 2, shape, strides);
            } else {
                shape = { rows, cols, channels };
                strides = { static_cast<ssize_t>(mat.step[0]), static_cast<ssize_t>(mat.step[1]), static_cast<ssize_t>(elem_size) };
                return py::buffer_info(mat.data, elem_size, format, 3, shape, strides);
            }
        });
}