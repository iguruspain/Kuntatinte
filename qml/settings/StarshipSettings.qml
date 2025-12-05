import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * StarshipSettings - Starship prompt color configuration.
 */
ColumnLayout {
    id: starshipSettings
    spacing: Kirigami.Units.smallSpacing
    
    // Action buttons row
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Label {
            text: "Starship"
            font.bold: true
        }
        
        Item { Layout.fillWidth: true }
        
        Controls.ToolButton {
            icon.name: "document-open"
            Controls.ToolTip.text: "Load current colors"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var colors = backend.loadStarshipColors()
                root.selectedAccent = colors.accent || ""
                root.selectedAccentText = colors.accent_text || ""
                root.selectedDirFg = colors.dir_fg || ""
                root.selectedDirBg = colors.dir_bg || ""
                root.selectedDirText = colors.dir_text || ""
                root.selectedGitFg = colors.git_fg || ""
                root.selectedGitBg = colors.git_bg || ""
                root.selectedGitText = colors.git_text || ""
                root.selectedOtherFg = colors.other_fg || ""
                root.selectedOtherBg = colors.other_bg || ""
                root.selectedOtherText = colors.other_text || ""
                root.accentSource = colors.accent ? "loaded" : ""
                root.accentTextSource = colors.accent_text ? "loaded" : ""
                root.dirFgSource = colors.dir_fg ? "loaded" : ""
                root.dirBgSource = colors.dir_bg ? "loaded" : ""
                root.dirTextSource = colors.dir_text ? "loaded" : ""
                root.gitFgSource = colors.git_fg ? "loaded" : ""
                root.gitBgSource = colors.git_bg ? "loaded" : ""
                root.gitTextSource = colors.git_text ? "loaded" : ""
                root.otherFgSource = colors.other_fg ? "loaded" : ""
                root.otherBgSource = colors.other_bg ? "loaded" : ""
                root.otherTextSource = colors.other_text ? "loaded" : ""
                root.showPassiveNotification("Starship colors loaded")
            }
        }
        
        Controls.ToolButton {
            icon.name: "edit-undo"
            Controls.ToolTip.text: "Restore from backup"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.restoreStarshipBackup()
                if (result === "") {
                    root.showPassiveNotification("Starship config restored from backup!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
        
        Controls.ToolButton {
            icon.name: "dialog-ok-apply"
            Controls.ToolTip.text: "Apply to Starship"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.applyStarshipColors(
                    root.selectedAccent, root.selectedAccentText,
                    root.selectedDirFg, root.selectedDirBg, root.selectedDirText,
                    root.selectedGitFg, root.selectedGitBg, root.selectedGitText,
                    root.selectedOtherFg, root.selectedOtherBg, root.selectedOtherText
                )
                if (result === "") {
                    root.showPassiveNotification("Starship colors applied!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
    }
    
    SubtleSeparator {}
    
    // Scrollable content
    Controls.ScrollView {
        id: starshipScrollView
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        
        Controls.ScrollBar.horizontal.policy: Controls.ScrollBar.AlwaysOff
        Controls.ScrollBar.vertical.policy: Controls.ScrollBar.AsNeeded
        
        ColumnLayout {
            width: starshipScrollView.availableWidth
            spacing: Kirigami.Units.smallSpacing
    
            // Accent colors section
            Controls.Label {
                text: "Prompt Colors"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
    
            ColorRow {
                label: "Accent"
                colorValue: root.selectedAccent
                colorSource: root.accentSource
                onPaletteClicked: {
                    root.selectedAccent = root.selectedColor
                    root.accentSource = "palette"
                    if (backend) backend.setAccentColor(root.selectedAccent)
                }
                onPickerColorSelected: function(color) {
                    root.selectedAccent = color
                    root.accentSource = "pick"
                    if (backend) backend.setAccentColor(color)
                }
            }
    
            ColorRow {
                label: "Accent Text"
                colorValue: root.selectedAccentText
                colorSource: root.accentTextSource
                onPaletteClicked: {
                    root.selectedAccentText = root.selectedColor
                    root.accentTextSource = "palette"
                    if (backend) backend.setAccentTextColor(root.selectedAccentText)
                }
                onPickerColorSelected: function(color) {
                    root.selectedAccentText = color
                    root.accentTextSource = "pick"
                    if (backend) backend.setAccentTextColor(color)
                }
            }
    
            SubtleSeparator {}
    
            // Directory section
            Controls.Label {
                text: "Directory Module"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
    
            ColorRow {
                label: "Foreground"
                colorValue: root.selectedDirFg
                colorSource: root.dirFgSource
                onPaletteClicked: { root.selectedDirFg = root.selectedColor; root.dirFgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedDirFg = color; root.dirFgSource = "pick" }
            }
    
            ColorRow {
                label: "Background"
                colorValue: root.selectedDirBg
                colorSource: root.dirBgSource
                onPaletteClicked: { root.selectedDirBg = root.selectedColor; root.dirBgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedDirBg = color; root.dirBgSource = "pick" }
            }
    
            ColorRow {
                label: "Text"
                colorValue: root.selectedDirText
                colorSource: root.dirTextSource
                onPaletteClicked: { root.selectedDirText = root.selectedColor; root.dirTextSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedDirText = color; root.dirTextSource = "pick" }
            }
    
            SubtleSeparator {}
    
            // Git section
            Controls.Label {
                text: "Git Module"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
    
            ColorRow {
                label: "Foreground"
                colorValue: root.selectedGitFg
                colorSource: root.gitFgSource
                onPaletteClicked: { root.selectedGitFg = root.selectedColor; root.gitFgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedGitFg = color; root.gitFgSource = "pick" }
            }
    
            ColorRow {
                label: "Background"
                colorValue: root.selectedGitBg
                colorSource: root.gitBgSource
                onPaletteClicked: { root.selectedGitBg = root.selectedColor; root.gitBgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedGitBg = color; root.gitBgSource = "pick" }
            }
    
            ColorRow {
                label: "Text"
                colorValue: root.selectedGitText
                colorSource: root.gitTextSource
                onPaletteClicked: { root.selectedGitText = root.selectedColor; root.gitTextSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedGitText = color; root.gitTextSource = "pick" }
            }
    
            SubtleSeparator {}
    
            // Other section
            Controls.Label {
                text: "Other Modules"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
            }
    
            ColorRow {
                label: "Foreground"
                colorValue: root.selectedOtherFg
                colorSource: root.otherFgSource
                onPaletteClicked: { root.selectedOtherFg = root.selectedColor; root.otherFgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedOtherFg = color; root.otherFgSource = "pick" }
            }
    
            ColorRow {
                label: "Background"
                colorValue: root.selectedOtherBg
                colorSource: root.otherBgSource
                onPaletteClicked: { root.selectedOtherBg = root.selectedColor; root.otherBgSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedOtherBg = color; root.otherBgSource = "pick" }
            }
    
            ColorRow {
                label: "Text"
                colorValue: root.selectedOtherText
                colorSource: root.otherTextSource
                onPaletteClicked: { root.selectedOtherText = root.selectedColor; root.otherTextSource = "palette" }
                onPickerColorSelected: function(color) { root.selectedOtherText = color; root.otherTextSource = "pick" }
            }
    
            Item { Layout.fillHeight: true }
        }
    }
}
