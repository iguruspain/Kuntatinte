import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * CentralPanel - Main content area with image preview and palette extraction.
 * 
 * Required properties from parent:
 * - root.leftPanelVisible: bool
 * - root.rightPanelVisible: bool
 * - root.selectedImagePath: string
 * - root.extractedColors: array
 * - root.extractedAccent: string
 * - root.selectedSwatchIndex: int
 * - root.extractionMethod: string
 * - backend: PaletteBackend
 */
ColumnLayout {
    id: centralPanel
    
    Layout.fillHeight: true
    Layout.fillWidth: true  // Expands to fill available space
    spacing: 0
    
    function getContrastTextColor(bgColor) {
        // Calculate luminance and return contrasting text color
        var r = parseInt(bgColor.slice(1,3), 16) / 255.0;
        var g = parseInt(bgColor.slice(3,5), 16) / 255.0;
        var b = parseInt(bgColor.slice(5,7), 16) / 255.0;
        var lum = 0.299 * r + 0.587 * g + 0.114 * b;
        return lum > 0.5 ? "#000000" : "#ffffff";
    }
    
    // Functions to control busy indicator (called from Main.qml)
    function showBusyIndicator() {
        busyIndicator.visible = true
    }
    
    function hideBusyIndicator() {
        busyIndicator.visible = false
    }
    
    // Panel header
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 56
        color: "transparent"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            anchors.leftMargin: Kirigami.Units.largeSpacing
            anchors.rightMargin: Kirigami.Units.largeSpacing
            
            Controls.ToolButton {
                icon.name: root.leftPanelVisible ? "sidebar-collapse-left" : "sidebar-expand-left"
                onClicked: root.leftPanelVisible = !root.leftPanelVisible
                Controls.ToolTip.text: root.leftPanelVisible ? "Hide Wallpapers" : "Show Wallpapers"
                Controls.ToolTip.visible: hovered
                Layout.alignment: Qt.AlignVCenter
            }
            
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                
                Kirigami.Heading {
                    text: {
                        if (!root.selectedImagePath) return "No image selected"
                        var parts = root.selectedImagePath.split("/")
                        return parts[parts.length - 1]
                    }
                    level: 2
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideMiddle
                }
                
                Controls.Label {
                    text: previewImage.status === Image.Ready ? 
                        previewImage.sourceSize.width + " × " + previewImage.sourceSize.height + " px" : ""
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                    opacity: 0.7
                    visible: root.selectedImagePath !== ""
                }
            }
            
            Controls.ToolButton {
                icon.name: root.rightPanelVisible ? "sidebar-collapse-right" : "sidebar-expand-right"
                onClicked: root.rightPanelVisible = !root.rightPanelVisible
                Controls.ToolTip.text: root.rightPanelVisible ? "Hide Settings" : "Show Settings"
                Controls.ToolTip.visible: hovered
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }
    
    // Subtle horizontal separator (not touching edges)
    Item {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            height: 1
            color: Kirigami.Theme.textColor
            opacity: 0.15
        }
    }
    
    // Panel content
    ColumnLayout {
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
        
        // Image preview - limited height to leave room for palette
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.maximumHeight: 300
            
            Image {
                id: previewImage
                anchors.fill: parent
                source: root.selectedImagePath ? "file://" + root.selectedImagePath : ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                
                readonly property real imageScale: {
                    if (sourceSize.width === 0 || sourceSize.height === 0) return 1
                    return Math.min(width / sourceSize.width, height / sourceSize.height)
                }
                readonly property real paintedWidth: sourceSize.width * imageScale
                readonly property real paintedHeight: sourceSize.height * imageScale
                readonly property real imageX: (width - paintedWidth) / 2
                readonly property real imageY: (height - paintedHeight) / 2
            }
            
            Controls.ToolButton {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: Kirigami.Units.smallSpacing
                anchors.bottomMargin: Kirigami.Units.smallSpacing
                visible: root.selectedImagePath !== "" && previewImage.status === Image.Ready
                icon.name: "viewimage"
                Controls.ToolTip.text: "Apply Wallpaper"
                onClicked: { if (backend) backend.setAsWallpaper(root.selectedImagePath) }
            }
            
            Controls.Label {
                anchors.centerIn: parent
                text: "Select a wallpaper"
                visible: !root.selectedImagePath
                opacity: 0.5
            }
        }
        
        // Extract palette button with method selector
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            
            Controls.ComboBox {
                id: extractionMethodCombo
                model: ["ImageMagick", "Material You", "Pywal"]
                currentIndex: {
                    switch(root.extractionMethod) {
                        case "Material You": return 1
                        case "Pywal": return 2
                        default: return 0  // ImageMagick
                    }
                }
                implicitWidth: 140
                
                // Flag to prevent extraction on initial load
                property bool initialized: false
                Component.onCompleted: initialized = true
                
                onCurrentTextChanged: {
                    root.extractionMethod = currentText
                    
                    // Reset palette UI when switching extraction method
                    // to avoid showing previous palette/accents sections.
                    if (!initialized) return
                    root.resetPaletteState()
                    // Do not auto-generate palette on method change; follow Extract button behavior
                }
            }

            // (Material You mode selector moved below, before the palette section)
            
            // (Removed) Color set selector for System extraction.
            
            Controls.ToolButton {
                icon.name: "color-picker"
                enabled: (root.selectedImagePath !== "" || root.extractionMethod === "Material You") && !busyIndicator.visible
                Controls.ToolTip.text: "Extract Palette"
                Controls.ToolTip.visible: hovered
                onClicked: {
                    if (!backend) return
                    busyIndicator.visible = true

                    if (root.extractionMethod === "Material You") {
                            // For Material You: extract accent and source colors. Generation
                            // will be triggered after source colors are returned.
                                if (root.selectedImagePath !== "") {
                                    backend.extractAccent(root.selectedImagePath)
                                    if (backend.isMaterialYouAvailable()) {
                                        backend.extractSourceColors(root.selectedImagePath)
                                    }
                                }
                        } else {
                        // Default behavior for other extraction methods
                        backend.extractColors(root.selectedImagePath, root.extractionMethod, root.paletteMode)
                        // Extract accent and source colors only if there's an image
                        if (root.selectedImagePath !== "") {
                            backend.extractAccent(root.selectedImagePath)
                            if (backend.isMaterialYouAvailable()) {
                                backend.extractSourceColors(root.selectedImagePath)
                            }
                        }
                    }
                }
            }

            // (Pywal uses its own extraction defaults; no Light/Dark selector)

            // Busy indicator for extraction/generation actions
            Controls.BusyIndicator {
                id: busyIndicator
                Layout.alignment: Qt.AlignVCenter
                visible: false
            }

        }

        // Color palette
        ColumnLayout {
            id: paletteColumn
            Layout.fillWidth: true
            spacing: 4
            opacity: root.extractedColors.length > 0 ? 1 : 0
            
            // === PALETTE SECTION ===
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Controls.Label {
                    text: "Palette"
                    font.bold: true
                    Layout.alignment: Qt.AlignVCenter
                }

                // Palette mode selector
                Controls.ButtonGroup {
                    id: paletteModeGroup
                }

                Controls.RadioButton {
                    text: "Light"
                    checked: root.paletteMode === "light"
                    Controls.ButtonGroup.group: paletteModeGroup
                    onClicked: root.paletteMode = "light"
                    visible: root.extractionMethod !== "Pywal"
                }

                Controls.RadioButton {
                    text: "Dark"
                    checked: root.paletteMode === "dark"
                    Controls.ButtonGroup.group: paletteModeGroup
                    onClicked: root.paletteMode = "dark"
                    visible: root.extractionMethod !== "Pywal"
                }

                // Busy indicator next to radio buttons
                Controls.BusyIndicator {
                    Layout.alignment: Qt.AlignVCenter
                    visible: busyIndicator.visible
                }
            }
            
            // First row of palette colors (0-7)
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: 8
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        color: index < root.extractedColors.length ? root.extractedColors[index] : "transparent"
                        border.color: root.selectedSwatchIndex === index && index < root.extractedColors.length ?
                            Kirigami.Theme.highlightColor : 
                            (index < root.extractedColors.length ? Qt.darker(root.extractedColors[index], 1.3) : Kirigami.Theme.disabledTextColor)
                        border.width: root.selectedSwatchIndex === index ? 3 : 1
                        radius: 4
                        Controls.ToolTip.text: index < root.extractedColors.length ? root.extractedColors[index] : ""
                        Controls.ToolTip.visible: swatchMouse1.containsMouse && index < root.extractedColors.length
                        MouseArea {
                            id: swatchMouse1
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            enabled: index < root.extractedColors.length
                            onClicked: function(mouse) {
                                if (mouse.button === Qt.RightButton) {
                                    var newColor = backend.pickColor()
                                    if (newColor !== "") {
                                        var colors = root.extractedColors.slice()
                                        colors[index] = newColor
                                        root.extractedColors = colors
                                    }
                                } else {
                                    root.selectedSwatchIndex = index
                                }
                            }
                        }
                    }
                }
            }
            
            // Second row of palette colors (8-15)
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: 8
                    Rectangle {
                        property int colorIndex: index + 8
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        color: colorIndex < root.extractedColors.length ? root.extractedColors[colorIndex] : "transparent"
                        border.color: root.selectedSwatchIndex === colorIndex && colorIndex < root.extractedColors.length ?
                            Kirigami.Theme.highlightColor : 
                            (colorIndex < root.extractedColors.length ? Qt.darker(root.extractedColors[colorIndex], 1.3) : Kirigami.Theme.disabledTextColor)
                        border.width: root.selectedSwatchIndex === colorIndex ? 3 : 1
                        radius: 4
                        Controls.ToolTip.text: colorIndex < root.extractedColors.length ? root.extractedColors[colorIndex] : ""
                        Controls.ToolTip.visible: swatchMouse2.containsMouse && colorIndex < root.extractedColors.length
                        MouseArea {
                            id: swatchMouse2
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            enabled: colorIndex < root.extractedColors.length
                            onClicked: function(mouse) {
                                if (mouse.button === Qt.RightButton) {
                                    var newColor = backend.pickColor()
                                    if (newColor !== "") {
                                        var colors = root.extractedColors.slice()
                                        colors[colorIndex] = newColor
                                        root.extractedColors = colors
                                    }
                                } else {
                                    root.selectedSwatchIndex = colorIndex
                                }
                            }
                        }
                    }
                }
            }
            
            // === RECOMMENDED ACCENTS SECTION ===
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                visible: root.extractedAccent !== "" || (root.sourceColors && root.sourceColors.length > 0)
                Controls.Label {
                    text: "Recommended Accents"
                    font.bold: true
                }
                Controls.Label {
                    text: "(select accent to change palette)"
                    font.italic: true
                    opacity: 0.7
                    visible: root.extractionMethod === "Material You"
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                visible: root.extractedAccent !== "" || (root.sourceColors && root.sourceColors.length > 0)
                
                // ImageMagick recommended accent
                Rectangle {
                    visible: root.extractedAccent !== ""
                    Layout.fillWidth: true
                    Layout.maximumWidth: (paletteColumn.width - 7 * 4) / 8
                    Layout.preferredHeight: 32
                    color: root.extractedAccent || "#3daee9"
                    border.color: root.selectedSwatchIndex === -2 ?
                        Kirigami.Theme.highlightColor : 
                        Qt.darker(root.extractedAccent || "#3daee9", 1.3)
                    border.width: root.selectedSwatchIndex === -2 ? 3 : 1
                    radius: 4
                    
                    // Removed star icon for ImageMagick accent (was decorative)
                    
                    Controls.ToolTip.text: (root.extractedAccent || "#3daee9") + " (ImageMagick)"
                    Controls.ToolTip.visible: extractedAccentSwatchMouse.containsMouse
                    MouseArea {
                        id: extractedAccentSwatchMouse
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: function(mouse) {
                            if (mouse.button === Qt.RightButton) {
                                var newColor = backend.pickColor()
                                if (newColor !== "") {
                                    root.extractedAccent = newColor
                                }
                            } else {
                                root.selectedSwatchIndex = -2
                            }
                        }
                    }
                }
                
                // Material You source colors
                Repeater {
                    id: sourceColorsRepeater
                    model: root.sourceColors
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.maximumWidth: (paletteColumn.width - 7 * 4) / 8
                        Layout.preferredHeight: 32
                        color: modelData
                        border.color: root.selectedSwatchIndex === (-100 - index) ?
                            Kirigami.Theme.highlightColor : 
                            Qt.darker(modelData, 1.3)
                        border.width: root.selectedSwatchIndex === (-100 - index) ? 3 : 1
                        radius: 4
                        
                        Kirigami.Icon {
                            anchors.centerIn: parent
                            width: 16
                            height: 16
                            source: "dialog-ok"
                            color: centralPanel.getContrastTextColor(modelData)
                            visible: root.selectedSwatchIndex === (-100 - index) && root.extractionMethod === "Material You"
                        }
                        
                        Controls.ToolTip.text: modelData + " (Material You #" + (index + 1) + ")"
                        Controls.ToolTip.visible: sourceColorMouse.containsMouse
                        
                        MouseArea {
                            id: sourceColorMouse
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            onClicked: {
                                root.selectedSwatchIndex = -100 - index
                                // If Material You mode active, regenerate palette using this seed
                                    if (root.extractionMethod === "Material You" && backend && backend.isMaterialYouAvailable()) {
                                        var sliderPercent = 50.0
                                    if (root.baseSourceColors && root.baseSourceColors.length > 0) {
                                        backend.generateMaterialYouPaletteFromSeeds(root.baseSourceColors, root.paletteMode, index, sliderPercent)
                                        } else {
                                            backend.generateMaterialYouPalette(root.selectedImagePath, index, sliderPercent)
                                        }
                                    }
                            }
                        }
                    }
                }
            }
            
            // === ACTION BUTTONS ===
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing
                
                Item { Layout.fillWidth: true }
                
                Controls.Button {
                    text: "Autogen"
                    icon.name: "system-run"
                    onClicked: {
                        // Instantiate and open AutogenDialog dynamically
                        try {
                            var comp = Qt.createComponent("AutogenDialog.qml")
                            if (comp.status === Component.Ready) {
                                var dlg = comp.createObject(root, { backend: backend, busyIndicator: busyIndicator })
                                if (dlg) dlg.open()
                                else console.log("Failed to create AutogenDialog object")
                            } else {
                                console.log("AutogenDialog component not ready:", comp.errorString())
                            }
                        } catch (e) {
                            console.log("Error creating AutogenDialog:", e)
                        }
                    }
                }
                
                Controls.Button {
                    text: "Apply"
                    icon.name: "dialog-ok-apply"
                    onClicked: {
                        // TODO: Implement apply functionality
                    }
                }
            }
        }
    }
}
