# ANPR (Automatic Number Plate Recognition) System

A comprehensive ANPR system built with Python that provides real-time license plate detection and recognition using computer vision and OCR technologies.

## 🚀 Features

- **Real-time License Plate Detection**: Uses YOLO model for accurate license plate detection
- **OCR Text Recognition**: PaddleOCR integration for robust text extraction
- **Multi-camera Support**: Simultaneous processing of entry and exit cameras
- **Modern GUI**: CustomTkinter-based interface with dark/light themes
- **Data Management**: Automatic CSV logging with image storage
- **Search & Analytics**: Built-in search functionality and data visualization
- **Duplicate Detection**: Smart filtering to prevent duplicate entries
- **Configurable Settings**: Easy camera IP and system configuration

## 🛠️ Technology Stack

- **Computer Vision**: OpenCV, YOLO (Ultralytics)
- **OCR**: PaddleOCR
- **GUI**: CustomTkinter
- **Data Processing**: Pandas, NumPy
- **Image Processing**: PIL, Deskew
- **Text Processing**: Levenshtein distance for similarity matching

## 📋 Prerequisites

- Python 3.8 or higher
- CUDA-compatible GPU (recommended for better performance)
- RTSP-compatible IP cameras

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AbdulBasithMohammed/ANPR.git
   cd ANPR
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your camera credentials and IP addresses
   ```

4. **Download the YOLO model**
   - Place your trained `LPDetector.pt` model file in the root directory
   - Or use a pre-trained model for testing

## ⚙️ Configuration

### Environment Variables (.env file)

```env
# Camera RTSP Credentials
RTSP_USERNAME=your_username
RTSP_PASSWORD=your_password

# Camera IP Addresses
CAMERA_IP_ENTRY=192.168.1.100
CAMERA_IP_EXIT=192.168.1.101

# Model Configuration
MODEL_PATH=LPDetector.pt
CONFIDENCE_THRESHOLD=0.5
OCR_CONFIDENCE_THRESHOLD=0.7

# Processing Settings
SKIP_FRAMES=20
UNIQUENESS_TIME_WINDOW=90
```

### Settings Configuration

The system uses `settings.json` for GUI preferences:
- Camera IP addresses
- Appearance mode (dark/light)
- Default data view

## 🚀 Usage

### Running the GUI Application

```bash
python app.py
```

The GUI provides:
- **Home**: Live camera feeds and ANPR controls
- **Total Data**: View recent detections in tabular format
- **Search**: Search license plates by date range
- **Settings**: Configure camera IPs and appearance

### Running the Core ANPR System

```bash
python main.py
```

This runs the core processing system that:
- Connects to RTSP cameras
- Processes video frames for license plate detection
- Performs OCR on detected plates
- Validates and stores results

## 📁 Project Structure

```
ANPR/
├── main.py              # Core ANPR processing
├── app.py               # GUI application
├── util.py              # Utility functions
├── mappings.py          # OCR character mappings
├── settings.json        # GUI configuration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── .gitignore          # Git ignore rules
├── LPDetector.pt       # YOLO model file
├── assets/             # GUI assets
│   ├── icons/          # Application icons
│   └── fonts/          # Custom fonts
└── output/             # Generated data (auto-created)
    ├── Entry DD-MM-YYYY/
    ├── Exit DD-MM-YYYY/
    └── *.csv files
```

## 🔍 Key Features Explained

### License Plate Detection
- Uses YOLO model for real-time object detection
- Processes every 20th frame for optimal performance
- Confidence threshold filtering (default: 0.5)

### OCR Processing
- PaddleOCR for text extraction
- Image preprocessing with deskewing and filtering
- Character mapping for common OCR errors
- Confidence threshold filtering (default: 0.7)

### Duplicate Prevention
- Time-based uniqueness checking (90-second window)
- Similarity matching using Levenshtein distance
- Automatic replacement of lower-confidence duplicates

### Data Storage
- Daily CSV files with comprehensive metadata
- Automatic image storage (full frame + cropped plate)
- Organized directory structure by date and camera type

## 🎯 License Plate Format Support

The system supports Indian license plate formats:
- **9 characters**: `XX#X##XXXX` or `XX##X#XXXX`
- **10 characters**: `XX##XX####`

Where:
- `X` = Letters
- `#` = Numbers

## 🔧 Troubleshooting

### Common Issues

1. **Camera Connection Failed**
   - Verify IP addresses and credentials in `.env`
   - Check network connectivity
   - Ensure RTSP stream is accessible

2. **Low Detection Accuracy**
   - Adjust confidence thresholds in `.env`
   - Check camera positioning and lighting
   - Retrain or update the YOLO model

3. **OCR Errors**
   - Review character mappings in `mappings.py`
   - Adjust image preprocessing parameters
   - Check license plate clarity and angle

### Performance Optimization

- Use GPU acceleration for YOLO and PaddleOCR
- Adjust `SKIP_FRAMES` for performance vs accuracy balance
- Monitor system resources during operation

## 📊 Output Data Format

CSV files contain the following columns:
- `SNo`: Sequential number
- `Camera`: Camera IP address
- `Entry/Exit`: Camera type
- `Date`: Detection date
- `Time`: Detection time
- `LicensePlate`: Recognized plate number
- `Confidence Score`: OCR confidence
- `Image Path`: Full frame image path
- `Cropped Image`: Cropped plate image path

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Abdul Basith Mohammed**
- GitHub: [@AbdulBasithMohammed](https://github.com/AbdulBasithMohammed)

## 🙏 Acknowledgments

- [Ultralytics](https://github.com/ultralytics/ultralytics) for YOLO implementation
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for OCR capabilities
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern GUI components

## 📞 Support

For support and questions, please open an issue on GitHub or contact the author.

---

**Note**: This system is designed for educational and research purposes. Ensure compliance with local privacy laws and regulations when deploying in production environments.
