#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>  // For NumPy support
#include <opencv2/videoio.hpp>  // For VideoCapture
#include <opencv2/imgproc.hpp>  // Optional, for any color conversions if needed
#include <stdexcept>  // For error handling

namespace py = pybind11;

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
        return frame;
    }

    void release() {
        cap.release();
    }

private:
    cv::VideoCapture cap;
};

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
            // Assume uchar data (common for images); adjust if your frames differ
            return py::buffer_info(
                mat.data,                               // Pointer to buffer
                sizeof(unsigned char),                  // Size of one scalar
                py::format_descriptor<unsigned char>::format(),  // Format descriptor
                3,                                      // Number of dimensions (height, width, channels)
                std::vector<ssize_t>{ mat.rows, mat.cols, mat.channels() }, // Shape
                std::vector<ssize_t>{ 
                    static_cast<ssize_t>(mat.step[0]),  // Row stride
                    static_cast<ssize_t>(mat.step[1]),  // Column stride
                    static_cast<ssize_t>(sizeof(unsigned char)) // Channel stride
                }
            );
        });
}