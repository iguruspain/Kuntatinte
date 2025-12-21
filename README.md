# Kuntatinte

Kuntatinte is a modern application for extracting color palettes from images using QML with Kirigami for a native KDE Plasma experience.

## Features

- **Advanced color extraction**: Uses Material You and ImageMagick algorithms to extract vibrant and harmonious color palettes
- **Multiple integrations**: Support for pywal, fastfetch, starship, ulauncher and KDE color schemes
- **Native interface**: QML interface with Kirigami for a smooth KDE Plasma experience
- **Kuntatinte schemes**: Generates complete color schemes based on Material You
- **Structured logging**: Complete logging system for debugging and monitoring
- **Type hints**: Code with type annotations for better maintainability

## Requirements

- Python 3.8+
- PyQt6 >= 6.0
- Pillow >= 9.0
- materialyoucolor >= 2.0.9
- pywal >= 3.3.0

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd kuntatinte
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python kuntatinte.py
   ```

## Usage

1. Open the application
2. Select a folder with images or load individual images
3. Choose an extraction method (ImageMagick, Material You, or pywal)
4. Extract colors and apply integrations as needed

## Project Structure

- `core/`: Main logic, color utilities, Qt backend
- `integrations/`: Modules for integrations with external tools
- `qml/`: QML user interface and Kirigami components
- `templates/`: Configuration templates for integrations

## Development

### Logging

The application uses structured logging. Logs are written to the console with appropriate levels (INFO, DEBUG, ERROR, WARNING).

### Contributing

1. Fork the project
2. Create a branch for your feature: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Create a Pull Request

## License

GPL-3.0