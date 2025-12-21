import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * FastfetchSettings - Fastfetch logo tinting configuration.
 */
ColumnLayout {
    id: fastfetchSettings
    spacing: Kirigami.Units.smallSpacing
    
    Connections {
        target: backend
        function onConfigChanged(section, key, value) {
            if (section === "fastfetch" && key === "accent") {
                root.fastfetchAccent = value
                root.fastfetchAccentSource = "config"
                // Update preview if available
                if (value) {
                    root.fastfetchPreviewTinted = backend.generateFastfetchPreview(value)
                }
            }
        }
    }
    
    // Action buttons row
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Label {
            text: "Fastfetch"
            font.bold: true
        }
        
        Item { Layout.fillWidth: true }
        
        Controls.ToolButton {
            icon.name: "edit-undo"
            Controls.ToolTip.text: "Restore from backup"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.restoreFastfetchOriginal()
                if (result === "") {
                    root.showPassiveNotification("Fastfetch logo restored from backup!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
        
        Controls.ToolButton {
            icon.name: "dialog-ok-apply"
            enabled: root.fastfetchAccent !== ""
            Controls.ToolTip.text: "Apply to Fastfetch"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.applyFastfetchAccent(root.fastfetchAccent)
                if (result === "") {
                    root.showPassiveNotification("Fastfetch logo tinted!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
    }
    
    SubtleSeparator {}
    
    // Scrollable content
    Controls.ScrollView {
        id: fastfetchScrollView
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        Controls.ScrollBar.horizontal.policy: Controls.ScrollBar.AlwaysOff
        Controls.ScrollBar.vertical.policy: Controls.ScrollBar.AsNeeded
        
        ColumnLayout {
            width: fastfetchScrollView.availableWidth
            spacing: Kirigami.Units.smallSpacing
            
            // Logo Template section
            Controls.Label {
                text: "Logo Template"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 28
                    color: "transparent"
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    radius: 4
                    
                    Controls.Label {
                        anchors.fill: parent
                        anchors.margins: 4
                        text: root.fastfetchLogoPath ? root.fastfetchLogoPath.replace(/^file:\/\//, '').split('/').pop() : "Default template"
                        elide: Text.ElideMiddle
                        verticalAlignment: Text.AlignVCenter
                        color: root.fastfetchLogoPath ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                        font.italic: !root.fastfetchLogoPath
                    }
                }
                
                Controls.ToolButton {
                    icon.name: "document-open"
                    Controls.ToolTip.text: "Select custom logo"
                    Controls.ToolTip.visible: hovered
                    onClicked: {
                        var path = backend.selectFastfetchLogo()
                        if (path) {
                            var result = backend.setFastfetchCustomLogo(path)
                            if (result === "") {
                                root.fastfetchLogoPath = path
                                root.fastfetchPreviewOriginal = backend.getFastfetchActiveLogo()
                                if (root.fastfetchAccent) {
                                    root.fastfetchPreviewTinted = backend.generateFastfetchPreview(root.fastfetchAccent)
                                }
                                root.showPassiveNotification("Custom logo set")
                            } else {
                                root.showPassiveNotification("Error: " + result)
                            }
                        }
                    }
                }
                
                Controls.ToolButton {
                    icon.name: "edit-clear"
                    enabled: root.fastfetchLogoPath !== ""
                    Controls.ToolTip.text: "Reset to default template"
                    Controls.ToolTip.visible: hovered
                    onClicked: {
                        var result = backend.resetFastfetchToDefault()
                        if (result === "") {
                            root.fastfetchLogoPath = ""
                            root.fastfetchPreviewOriginal = backend.getFastfetchActiveLogo()
                            if (root.fastfetchAccent) {
                                root.fastfetchPreviewTinted = backend.generateFastfetchPreview(root.fastfetchAccent)
                            }
                            root.showPassiveNotification("Reset to default template")
                        } else {
                            root.showPassiveNotification("Error: " + result)
                        }
                    }
                }
            }
            
            SubtleSeparator {}
            
            // Tint Color section
            Controls.Label {
                text: "Tint Color"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
            
            ColorRow {
                label: "Accent"
                colorValue: root.fastfetchAccent
                colorSource: root.fastfetchAccentSource
                onPaletteClicked: {
                    root.fastfetchAccent = root.selectedColor
                    root.fastfetchAccentSource = "palette"
                    root.fastfetchPreviewTinted = backend.generateFastfetchPreview(root.fastfetchAccent)
                }
                onPickerColorSelected: function(color) {
                    root.fastfetchAccent = color
                    root.fastfetchAccentSource = "pick"
                    root.fastfetchPreviewTinted = backend.generateFastfetchPreview(root.fastfetchAccent)
                }
            }
            
            SubtleSeparator {}
            
            // Preview section
            Controls.Label {
                text: "Preview"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
            
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing
                
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    
                    Image {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        source: root.fastfetchPreviewOriginal
                        fillMode: Image.PreserveAspectFit
                        cache: false
                    }
                    
                    Controls.Label {
                        Layout.fillWidth: true
                        text: "Source"
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    visible: root.fastfetchPreviewTinted !== ""
                    
                    Image {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        source: root.fastfetchPreviewTinted
                        fillMode: Image.PreserveAspectFit
                        cache: false
                    }
                    
                    Controls.Label {
                        Layout.fillWidth: true
                        text: "Tinted"
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
    
    Component.onCompleted: {
        root.fastfetchLogoPath = backend.getFastfetchActiveLogo()
        root.fastfetchPreviewOriginal = backend.getFastfetchActiveLogo()
    }
}
