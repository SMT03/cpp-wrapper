#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>  // For NumPy support
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>  // For color conversions
#include <stdexcept>  // For error handling
#include <iostream>

// FFmpeg libraries for RTSP decoding with rkmpp hardware acceleration
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_drm.h>
#include <libswscale/swscale.h>

// RGA for hardware color conversion (Rockchip)
extern "C" {
#include <rga/rga.h>
#include <rga/im2d.h>
}

namespace py = pybind11;

// RTSPReader using jellyfin-ffmpeg with rkmpp hardware decoding and RGA conversion
class RTSPReader {
public:
    RTSPReader(const std::string& url) : fmt_ctx(nullptr), codec_ctx(nullptr), hw_device_ctx(nullptr), 
                                          sws_ctx(nullptr), video_stream_index(-1), use_rga(true) {
        avformat_network_init();
        
        // Open RTSP stream with minimal buffering (1 frame)
        AVDictionary* opts = nullptr;
        av_dict_set(&opts, "rtsp_transport", "tcp", 0);
        av_dict_set(&opts, "buffer_size", "1", 0);  // 1 frame buffer
        av_dict_set(&opts, "max_delay", "0", 0);     // Minimal delay
        av_dict_set(&opts, "reorder_queue_size", "1", 0);  // Reorder queue size
        
        if (avformat_open_input(&fmt_ctx, url.c_str(), nullptr, &opts) != 0) {
            av_dict_free(&opts);
            throw std::runtime_error("Failed to open RTSP stream: " + url);
        }
        av_dict_free(&opts);
        
        if (avformat_find_stream_info(fmt_ctx, nullptr) < 0) {
            cleanup();
            throw std::runtime_error("Failed to find stream info");
        }

        // Find video stream
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
        
        // Try to find rkmpp decoder first
        const AVCodec* codec = nullptr;
        if (codecpar->codec_id == AV_CODEC_ID_H264) {
            codec = avcodec_find_decoder_by_name("h264_rkmpp");
            if (!codec) {
                std::cerr << "Warning: h264_rkmpp not found, trying h264_rkmpp_decoder" << std::endl;
                codec = avcodec_find_decoder_by_name("h264_rkmpp_decoder");
            }
        } else if (codecpar->codec_id == AV_CODEC_ID_HEVC) {
            codec = avcodec_find_decoder_by_name("hevc_rkmpp");
            if (!codec) {
                codec = avcodec_find_decoder_by_name("hevc_rkmpp_decoder");
            }
        }
        
        // Fallback to default decoder if rkmpp not available
        if (!codec) {
            std::cerr << "Warning: rkmpp decoder not found, using software decoder" << std::endl;
            codec = avcodec_find_decoder(codecpar->codec_id);
            use_rga = false; // Can't use RGA without hardware frames
        }
        
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

        // Enable hardware decoding if using rkmpp
        if (use_rga) {
            // Set hardware device type (DRM for rkmpp)
            if (av_hwdevice_ctx_create(&hw_device_ctx, AV_HWDEVICE_TYPE_DRM, nullptr, nullptr, 0) < 0) {
                std::cerr << "Warning: Failed to create DRM device context, falling back to software" << std::endl;
                use_rga = false;
            } else {
                codec_ctx->hw_device_ctx = av_buffer_ref(hw_device_ctx);
                codec_ctx->get_format = get_hw_format;
            }
        }

        if (avcodec_open2(codec_ctx, codec, nullptr) < 0) {
            cleanup();
            throw std::runtime_error("Failed to open codec");
        }

        pkt = av_packet_alloc();
        frame = av_frame_alloc();
        hw_frame = av_frame_alloc();
        
        std::cout << "RTSPReader initialized with " 
                  << (use_rga ? "rkmpp hardware decoding" : "software decoding") << std::endl;
    }
    
    static enum AVPixelFormat get_hw_format(AVCodecContext *ctx, const enum AVPixelFormat *pix_fmts) {
        const enum AVPixelFormat *p;
        for (p = pix_fmts; *p != AV_PIX_FMT_NONE; p++) {
            if (*p == AV_PIX_FMT_DRM_PRIME) {
                return *p;
            }
        }
        return AV_PIX_FMT_NONE;
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

                AVFrame* src_frame = frame;
                
                // If using hardware decoding, transfer from GPU to CPU if needed
                if (use_rga && frame->format == AV_PIX_FMT_DRM_PRIME) {
                    if (av_hwframe_transfer_data(hw_frame, frame, 0) < 0) {
                        std::cerr << "Warning: Failed to transfer hwframe, falling back to software" << std::endl;
                        use_rga = false;
                        continue;
                    }
                    src_frame = hw_frame;
                }

                // Convert to BGR
                int width = src_frame->width;
                int height = src_frame->height;
                int src_format = src_frame->format;
                
                cv::Mat out_mat(height, width, CV_8UC3);
                
                // Try RGA conversion if available (much faster on RK3588)
                if (use_rga && src_format == AV_PIX_FMT_NV12) {
                    if (convert_with_rga(src_frame, out_mat)) {
                        return out_mat;
                    } else {
                        std::cerr << "RGA conversion failed, falling back to swscale" << std::endl;
                        use_rga = false;
                    }
                }
                
                // Fallback to software swscale conversion
                SwsContext* local_sws = sws_getContext(
                    width, height, (AVPixelFormat)src_format,
                    width, height, AV_PIX_FMT_BGR24,
                    SWS_BILINEAR, nullptr, nullptr, nullptr
                );
                
                if (!local_sws) {
                    throw std::runtime_error("Failed to create sws context");
                }

                uint8_t* dest[4] = { out_mat.data, nullptr, nullptr, nullptr };
                int dest_linesize[4] = { static_cast<int>(out_mat.step[0]), 0, 0, 0 };

                sws_scale(local_sws, src_frame->data, src_frame->linesize, 0, height, dest, dest_linesize);
                sws_freeContext(local_sws);

                return out_mat;
            }
            av_packet_unref(pkt);
        }
        // If we exit loop, stream ended or error
        throw std::runtime_error("Failed to read frame from RTSP stream (EOF or error)");
    }

    void release() {
        // Destructor handles cleanup
    }

private:
    AVFormatContext* fmt_ctx;
    AVCodecContext* codec_ctx;
    AVBufferRef* hw_device_ctx;
    AVPacket* pkt;
    AVFrame* frame;
    AVFrame* hw_frame;
    SwsContext* sws_ctx;
    int video_stream_index;
    bool use_rga;
    
    bool convert_with_rga(AVFrame* src_frame, cv::Mat& dst) {
        // RGA conversion from NV12 to BGR using im2d API
        rga_buffer_t src_buf, dst_buf;
        memset(&src_buf, 0, sizeof(src_buf));
        memset(&dst_buf, 0, sizeof(dst_buf));
        
        // Setup source buffer (NV12)
        src_buf.width = src_frame->width;
        src_buf.height = src_frame->height;
        src_buf.format = RK_FORMAT_YCbCr_420_SP; // NV12
        src_buf.vir_addr = (void*)src_frame->data[0];
        
        // Setup destination buffer (BGR)
        dst_buf.width = dst.cols;
        dst_buf.height = dst.rows;
        dst_buf.format = RK_FORMAT_BGR_888;
        dst_buf.vir_addr = (void*)dst.data;
        
        // Perform conversion
        im_rect src_rect = {0, 0, src_frame->width, src_frame->height};
        im_rect dst_rect = {0, 0, dst.cols, dst.rows};
        
        int ret = imcvtcolor(src_buf, dst_buf, src_rect, dst_rect, IM_COLOR_SPACE_DEFAULT);
        
        return ret == IM_STATUS_SUCCESS;
    }

    void cleanup() {
        if (pkt) { av_packet_free(&pkt); pkt = nullptr; }
        if (frame) { av_frame_free(&frame); frame = nullptr; }
        if (hw_frame) { av_frame_free(&hw_frame); hw_frame = nullptr; }
        if (codec_ctx) { avcodec_free_context(&codec_ctx); codec_ctx = nullptr; }
        if (fmt_ctx) { avformat_close_input(&fmt_ctx); fmt_ctx = nullptr; }
        if (hw_device_ctx) { av_buffer_unref(&hw_device_ctx); hw_device_ctx = nullptr; }
        avformat_network_deinit();
    }
};

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