import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * OpenRGBSettings - OpenRGB color configuration.
 */
ColumnLayout {
    id: openrgbSettings
    spacing: Kirigami.Units.smallSpacing
    
    // Action buttons row
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Label {
            text: "OpenRGB"
            font.bold: true
        }
        
        Item { Layout.fillWidth: true }
        
        Controls.ToolButton {
            icon.name: "dialog-ok-apply"
            enabled: root.openrgbAccent !== "" && root.openrgbAccent.length === 6 && /^[0-9a-fA-F]{6}$/.test(root.openrgbAccent)
            Controls.ToolTip.text: "Apply to OpenRGB"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.applyOpenRGB(root.openrgbAccent)
                if (result === "") {
                    root.showPassiveNotification("OpenRGB color applied!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
    }
    
    SubtleSeparator {}
    
    // Scrollable content
    Controls.ScrollView {
        id: openrgbScrollView
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        Controls.ScrollBar.horizontal.policy: Controls.ScrollBar.AlwaysOff
        Controls.ScrollBar.vertical.policy: Controls.ScrollBar.AsNeeded
        
        ColumnLayout {
            width: openrgbScrollView.availableWidth
            spacing: Kirigami.Units.smallSpacing
            
            // Accent Color section
            Controls.Label {
                text: "Accent Color"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
            
            ColorRow {
                label: "Accent"
                colorValue: root.openrgbAccent ? "#" + root.openrgbAccent : ""
                colorSource: root.openrgbAccentSource
                onPaletteClicked: {
                    root.openrgbAccent = root.selectedColor.replace("#", "")
                    root.openrgbAccentSource = "palette"
                }
                onPickerColorSelected: function(color) {
                    root.openrgbAccent = color.replace("#", "")
                    root.openrgbAccentSource = "pick"
                }
            }
            
            Controls.Label {
                text: "Enter a 6-digit hex color code (without #) to set as the accent color for OpenRGB."
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
}