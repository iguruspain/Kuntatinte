import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * UlauncherSettings - Ulauncher theme color configuration.
 */
ColumnLayout {
    id: ulauncherSettings
    spacing: Kirigami.Units.smallSpacing
    
    // Action buttons row
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Label {
            text: "Ulauncher"
            font.bold: true
        }
        
        Item { Layout.fillWidth: true }
        
        Controls.ToolButton {
            icon.name: "document-open"
            Controls.ToolTip.text: "Load current colors"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var colors = backend.loadUlauncherColors()
                if (colors) {
                    root.ulauncherBgColor = colors.bg_color || ""
                    root.ulauncherBorderColor = colors.window_border_color || ""
                    root.ulauncherBgOpacity = colors.bg_color_opacity || 100
                    root.ulauncherBorderOpacity = colors.window_border_color_opacity || 100
                    root.ulauncherPrefsBackground = colors.prefs_background || ""
                    root.ulauncherInputColor = colors.input_color || ""
                    root.ulauncherSelectedBgColor = colors.selected_bg_color || ""
                    root.ulauncherSelectedFgColor = colors.selected_fg_color || ""
                    root.ulauncherItemName = colors.item_name || ""
                    root.ulauncherItemText = colors.item_text || ""
                    root.ulauncherShortcutColor = colors.item_shortcut_color || ""
                    root.ulauncherItemBoxSelected = colors.item_box_selected || ""
                    root.ulauncherItemNameSelected = colors.item_name_selected || ""
                    root.ulauncherItemTextSelected = colors.item_text_selected || ""
                    root.ulauncherShortcutColorSel = colors.item_shortcut_color_sel || ""
                    root.ulauncherWhenSelected = colors.when_selected || ""
                    root.ulauncherWhenNotSelected = colors.when_not_selected || ""
                    root.showPassiveNotification("Ulauncher colors loaded")
                }
            }
        }
        
        Controls.ToolButton {
            icon.name: "edit-undo"
            Controls.ToolTip.text: "Restore from backup"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.restoreUlauncherBackup()
                if (result === "") {
                    root.showPassiveNotification("Ulauncher theme restored from backup!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
        
        Controls.ToolButton {
            icon.name: "dialog-ok-apply"
            Controls.ToolTip.text: "Apply to Ulauncher"
            Controls.ToolTip.visible: hovered
            onClicked: {
                var result = backend.applyUlauncherColors(
                    root.ulauncherBgColor, root.ulauncherBorderColor,
                    root.ulauncherBgOpacity, root.ulauncherBorderOpacity,
                    root.ulauncherPrefsBackground, root.ulauncherInputColor,
                    root.ulauncherSelectedBgColor, root.ulauncherSelectedFgColor,
                    root.ulauncherItemName, root.ulauncherItemText,
                    root.ulauncherItemBoxSelected, root.ulauncherItemNameSelected,
                    root.ulauncherItemTextSelected, root.ulauncherShortcutColor,
                    root.ulauncherShortcutColorSel,
                    root.ulauncherWhenSelected, root.ulauncherWhenNotSelected
                )
                if (result === "") {
                    root.showPassiveNotification("Ulauncher theme applied!")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
    }
    
    SubtleSeparator {}
    
    // Tab bar for CSS vs JSON
    Controls.TabBar {
        id: ulauncherTabBar
        Layout.fillWidth: true
        
        Controls.TabButton {
            text: "theme.css"
        }
        Controls.TabButton {
            text: "manifest.json"
        }
    }
    
    // Tab content
    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: ulauncherTabBar.currentIndex
        
        // theme.css tab
        Controls.ScrollView {
            id: ulauncherCssScrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ColumnLayout {
                id: cssColorsColumn
                width: ulauncherCssScrollView.availableWidth
                spacing: Kirigami.Units.smallSpacing
            
                // App Window section (rgba_color = with opacity)
                Controls.Label {
                    text: "App Window"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                    Layout.topMargin: Kirigami.Units.smallSpacing
                }
                
                ColorRow {
                    label: "Background"
                    colorValue: root.ulauncherBgColor
                    colorSource: root.ulauncherBgColorSource
                    showOpacity: true
                    colorOpacity: root.ulauncherBgOpacity
                    onPaletteClicked: { root.ulauncherBgColor = root.selectedColor; root.ulauncherBgColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherBgColor = color; root.ulauncherBgColorSource = "pick" }
                    onOpacityModified: function(value) { root.ulauncherBgOpacity = value }
                }
                
                ColorRow {
                    label: "Border"
                    colorValue: root.ulauncherBorderColor
                    colorSource: root.ulauncherBorderColorSource
                    showOpacity: true
                    colorOpacity: root.ulauncherBorderOpacity
                    onPaletteClicked: { root.ulauncherBorderColor = root.selectedColor; root.ulauncherBorderColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherBorderColor = color; root.ulauncherBorderColorSource = "pick" }
                    onOpacityModified: function(value) { root.ulauncherBorderOpacity = value }
                }
                
                ColorRow {
                    label: "Prefs Button"
                    colorValue: root.ulauncherPrefsBackground
                    colorSource: root.ulauncherPrefsBackgroundSource
                    onPaletteClicked: { root.ulauncherPrefsBackground = root.selectedColor; root.ulauncherPrefsBackgroundSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherPrefsBackground = color; root.ulauncherPrefsBackgroundSource = "pick" }
                }
                
                SubtleSeparator {}
                
                // Input section
                Controls.Label {
                    text: "Input"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }
                
                ColorRow {
                    label: "Text Color"
                    colorValue: root.ulauncherInputColor
                    colorSource: root.ulauncherInputColorSource
                    onPaletteClicked: { root.ulauncherInputColor = root.selectedColor; root.ulauncherInputColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherInputColor = color; root.ulauncherInputColorSource = "pick" }
                }
                
                ColorRow {
                    label: "Selection Bg"
                    colorValue: root.ulauncherSelectedBgColor
                    colorSource: root.ulauncherSelectedBgColorSource
                    onPaletteClicked: { root.ulauncherSelectedBgColor = root.selectedColor; root.ulauncherSelectedBgColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherSelectedBgColor = color; root.ulauncherSelectedBgColorSource = "pick" }
                }
                
                ColorRow {
                    label: "Selection Fg"
                    colorValue: root.ulauncherSelectedFgColor
                    colorSource: root.ulauncherSelectedFgColorSource
                    onPaletteClicked: { root.ulauncherSelectedFgColor = root.selectedColor; root.ulauncherSelectedFgColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherSelectedFgColor = color; root.ulauncherSelectedFgColorSource = "pick" }
                }
                
                SubtleSeparator {}
                
                // Result Items section
                Controls.Label {
                    text: "Result Items"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }
                
                ColorRow {
                    label: "Name"
                    colorValue: root.ulauncherItemName
                    colorSource: root.ulauncherItemNameSource
                    onPaletteClicked: { root.ulauncherItemName = root.selectedColor; root.ulauncherItemNameSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherItemName = color; root.ulauncherItemNameSource = "pick" }
                }
                
                ColorRow {
                    label: "Description"
                    colorValue: root.ulauncherItemText
                    colorSource: root.ulauncherItemTextSource
                    onPaletteClicked: { root.ulauncherItemText = root.selectedColor; root.ulauncherItemTextSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherItemText = color; root.ulauncherItemTextSource = "pick" }
                }
                
                SubtleSeparator {}
                
                // Selected Result Items section
                Controls.Label {
                    text: "Selected Result Items"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }
                
                ColorRow {
                    label: "Background"
                    colorValue: root.ulauncherItemBoxSelected
                    colorSource: root.ulauncherItemBoxSelectedSource
                    onPaletteClicked: { root.ulauncherItemBoxSelected = root.selectedColor; root.ulauncherItemBoxSelectedSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherItemBoxSelected = color; root.ulauncherItemBoxSelectedSource = "pick" }
                }
                
                ColorRow {
                    label: "Name"
                    colorValue: root.ulauncherItemNameSelected
                    colorSource: root.ulauncherItemNameSelectedSource
                    onPaletteClicked: { root.ulauncherItemNameSelected = root.selectedColor; root.ulauncherItemNameSelectedSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherItemNameSelected = color; root.ulauncherItemNameSelectedSource = "pick" }
                }
                
                ColorRow {
                    label: "Description"
                    colorValue: root.ulauncherItemTextSelected
                    colorSource: root.ulauncherItemTextSelectedSource
                    onPaletteClicked: { root.ulauncherItemTextSelected = root.selectedColor; root.ulauncherItemTextSelectedSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherItemTextSelected = color; root.ulauncherItemTextSelectedSource = "pick" }
                }
                
                SubtleSeparator {}
                
                // Shortcuts section
                Controls.Label {
                    text: "Shortcuts"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }
                
                ColorRow {
                    label: "Color"
                    colorValue: root.ulauncherShortcutColor
                    colorSource: root.ulauncherShortcutColorSource
                    onPaletteClicked: { root.ulauncherShortcutColor = root.selectedColor; root.ulauncherShortcutColorSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherShortcutColor = color; root.ulauncherShortcutColorSource = "pick" }
                }
                
                SubtleSeparator {}
                
                // Selected Shortcuts section
                Controls.Label {
                    text: "Selected Shortcuts"
                    font.bold: true
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }
                
                ColorRow {
                    label: "Color"
                    colorValue: root.ulauncherShortcutColorSel
                    colorSource: root.ulauncherShortcutColorSelSource
                    onPaletteClicked: { root.ulauncherShortcutColorSel = root.selectedColor; root.ulauncherShortcutColorSelSource = "palette" }
                    onPickerColorSelected: function(color) { root.ulauncherShortcutColorSel = color; root.ulauncherShortcutColorSelSource = "pick" }
                }
                
                Item { Layout.fillHeight: true }
            }
        }
        
        // manifest.json tab
        ColumnLayout {
            id: jsonColorsColumn
            spacing: Kirigami.Units.smallSpacing
            
            // Matched text highlight section
            Controls.Label {
                text: "Matched Text Highlight"
                font.bold: true
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                color: Kirigami.Theme.disabledTextColor
                Layout.topMargin: Kirigami.Units.smallSpacing
            }
            
            ColorRow {
                label: "Selected"
                colorValue: root.ulauncherWhenSelected
                colorSource: root.ulauncherWhenSelectedSource
                onPaletteClicked: { root.ulauncherWhenSelected = root.selectedColor; root.ulauncherWhenSelectedSource = "palette" }
                onPickerColorSelected: function(color) { root.ulauncherWhenSelected = color; root.ulauncherWhenSelectedSource = "pick" }
            }
            
            ColorRow {
                label: "Unselected"
                colorValue: root.ulauncherWhenNotSelected
                colorSource: root.ulauncherWhenNotSelectedSource
                onPaletteClicked: { root.ulauncherWhenNotSelected = root.selectedColor; root.ulauncherWhenNotSelectedSource = "palette" }
                onPickerColorSelected: function(color) { root.ulauncherWhenNotSelected = color; root.ulauncherWhenNotSelectedSource = "pick" }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
    
    Item { Layout.fillHeight: true }
}
