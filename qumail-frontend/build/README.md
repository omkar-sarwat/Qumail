# Icon Assets

Place your application icons in this directory:

## Required Files

### Windows
- `icon.ico` - 256x256 icon for Windows application

### macOS
- `icon.icns` - Icon set for macOS application
- `entitlements.mac.plist` - Entitlements for code signing

### Linux
- `icon.png` - 512x512 PNG icon for Linux

## Generating Icons

### From PNG (512x512)

**Windows ICO**:
```bash
# Using ImageMagick
magick convert icon.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico

# Or use online tool: https://icoconvert.com/
```

**macOS ICNS**:
```bash
# Create iconset
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
cp icon.png icon.iconset/icon_512x512@2x.png

# Convert to ICNS
iconutil -c icns icon.iconset
```

## Default Icon

A basic placeholder icon is included. For production, replace with your branded icon.

## Icon Design Guidelines

- **Size**: Start with 1024x1024 or 512x512
- **Format**: PNG with transparency
- **Style**: Simple, recognizable at small sizes
- **Colors**: High contrast for visibility
- **Theme**: Quantum/security themed for QuMail

## Resources

- [Electron Icon Guide](https://www.electron.build/icons)
- [IconGenerator](https://icongeneratorapp.com/)
- [Figma](https://www.figma.com/) - Design custom icons
