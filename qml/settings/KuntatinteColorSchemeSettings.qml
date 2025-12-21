import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/*
 * KuntatinteColorSchemeSettings - Renamed from KdeColorScheme2Settings.
 * Generates "Kuntatinte Dark" and "Kuntatinte Light" color schemes
 * from the extracted color palette (Material You style).
 */
Controls.ScrollView {
    id: kdeSettings2
    visible: settingsPanel.currentSettingName === "Kuntatinte Color Scheme"
    Layout.fillWidth: true
    Layout.fillHeight: true
    contentWidth: availableWidth
    clip: true
    
    // Selected primary color index:
    //   -1: ImageMagick accent (default if available)
    //   -100 to -199: Material You source colors
    //   >= 0: Palette colors
    property int primaryColorIndex: root.extractedAccent && root.extractedAccent !== "" 
        ? -1 
        : (root.sourceColors && root.sourceColors.length > 0 ? -100 : 0)
    property int toolbarOpacity: 100
    property var previewData: ({})
    property bool generateExpanded: true
    property bool editExpanded: false
    property var kuntatinteSchemesList: []
    property string editSchemeName: ""
    property var editSchemeData: ({})
    property var editSchemeSections: []
    property var editInactiveSections: []
    // Temporary holders used to delay assigning data to UI-bound properties
    property var pendingEditSchemeData: null
    property var pendingEditSchemeSections: []
    property var pendingEditSchemeInactive: []
    property int schemeVariant: 5  // TonalSpot default
    
    ListModel {
        id: schemeVariantsModel
        ListElement { text: "Content"; value: 0 }
        ListElement { text: "Expressive"; value: 1 }
        ListElement { text: "Fidelity"; value: 2 }
        ListElement { text: "Monochrome"; value: 3 }
        ListElement { text: "Neutral"; value: 4 }
        ListElement { text: "TonalSpot"; value: 5 }
        ListElement { text: "Vibrant"; value: 6 }
        ListElement { text: "Rainbow"; value: 7 }
        ListElement { text: "FruitSalad"; value: 8 }
    }
    
    // Helper function to get contrast text color (black/white) for a given background color
    function getContrastTextColor(bgColor) {
        if (!bgColor || bgColor === "") return "white"
        var c = Qt.lighter(bgColor, 1.5)
        if (!c) return "white"
        return c.hslLightness > 0.5 ? "black" : "white"
    }
    
    // Helper function to get the selected color hex value
    // primaryColorIndex values:
    //   -1: ImageMagick recommended accent (root.extractedAccent)
    //   -100 to -199: Material You source colors (sourceColors[0], sourceColors[1], etc.)
    //   >= 0: Palette colors (extractedColors[index])
    function getSelectedColor() {
        if (primaryColorIndex === -1) {
            // ImageMagick recommended accent
            return root.extractedAccent || "#3daee9"
        } else if (primaryColorIndex <= -100) {
            // Source color: -100 = index 0, -101 = index 1, etc.
            var sourceIndex = -100 - primaryColorIndex
            if (root.sourceColors && sourceIndex < root.sourceColors.length) {
                return root.sourceColors[sourceIndex]
            }
        } else if (primaryColorIndex >= 0 && primaryColorIndex < root.extractedColors.length) {
            return root.extractedColors[primaryColorIndex]
        }
        // Fallback
        return root.extractedAccent || (root.extractedColors.length > 0 ? root.extractedColors[0] : "#3daee9")
    }
    
    // Functions
    function updatePreview() {
        var hasColors = root.extractedColors.length > 0 || (root.sourceColors && root.sourceColors.length > 0)
        if (hasColors) {
            var selectedColor = kdeSettings2.getSelectedColor()
            previewData = backend.getKuntatintePreview(
                root.extractedColors,
                kdeSettings2.primaryColorIndex >= 0 ? kdeSettings2.primaryColorIndex : -1,
                kdeSettings2.primaryColorIndex < 0 ? selectedColor : "",
                schemeVariant
            )
        }
    }
    
    // Update preview when palette or source colors change
    Connections {
        target: root
        function onExtractedColorsChanged() {
            if (root.sourceColors && root.sourceColors.length > 0) {
                kdeSettings2.primaryColorIndex = -100
            } else if (root.extractedColors.length > 0) {
                kdeSettings2.primaryColorIndex = 0
            }
            updatePreview()
        }
        function onSourceColorsChanged() {
            if (root.sourceColors && root.sourceColors.length > 0) {
                kdeSettings2.primaryColorIndex = -100
                updatePreview()
            }
        }
    }
    
    // Initial preview
    Component.onCompleted: {
        if (root.extractedColors.length > 0 || (root.sourceColors && root.sourceColors.length > 0)) {
            updatePreview()
        }
        // Auto-reload available Kuntatinte schemes at startup
        reloadKuntatinteSchemes()
        // Load config values
        schemeVariant = backend.getConfigValue("color_scheme", "scheme_variant", 5)
    }

    // Reload list of Kuntatinte schemes and (optionally) the selected scheme data
    function reloadKuntatinteSchemes() {
        try {
            var all = backend.getColorSchemesList()
            var res = []
            for (var i = 0; i < all.length; i++) {
                if (all[i] && typeof all[i] === "string" && all[i].indexOf("Kuntatinte") !== -1) res.push(all[i])
            }
            kuntatinteSchemesList = res

            // If a scheme was previously selected, reload its data
            if (editSchemeName && editSchemeName !== "") {
                try {
                    editSchemeData = backend.getFullSchemeData(editSchemeName)
                } catch (e) {
                    console.log('Error getting full scheme data for', editSchemeName, e)
                    editSchemeData = {}
                }
                try {
                    editSchemeSections = backend.getColorSections(editSchemeName)
                } catch (e) {
                    console.log('Error getting color sections for', editSchemeName, e)
                    editSchemeSections = []
                }
                try {
                    editInactiveSections = backend.getInactiveSections(editSchemeName)
                } catch (e) {
                    editInactiveSections = []
                }
            }

            // After reloading the list, auto-select a scheme and populate the editor
            if (kuntatinteSchemesList && kuntatinteSchemesList.length > 0) {
                var chosen = ""
                if (editSchemeName && kuntatinteSchemesList.indexOf(editSchemeName) !== -1) {
                    chosen = editSchemeName
                } else {
                    chosen = kuntatinteSchemesList[0]
                }
                // set combobox index (this will update displayText)
                try {
                    kuntatinteCombo.currentIndex = kuntatinteSchemesList.indexOf(chosen)
                } catch (e) {
                    // ignore if combo not yet ready
                }

                // fetch data and assign via deferred pending props (to avoid TabBar race)
                var pdata = {}
                try { pdata = backend.getFullSchemeData(chosen) } catch (e) { pdata = {} }
                var psecs = []
                try { psecs = backend.getColorSections(chosen) } catch (e) { var tmp = []; for (var k in pdata) tmp.push(k); psecs = tmp.sort() }
                var pinactive = []
                try { pinactive = backend.getInactiveSections(chosen) } catch (e) { pinactive = [] }

                kdeSettings2.pendingEditSchemeData = pdata
                kdeSettings2.pendingEditSchemeSections = psecs
                kdeSettings2.pendingEditSchemeInactive = pinactive
                delayedAssignTimer.start()
            }
        } catch (e) {
            console.log('Error loading kuntatinte schemes list:', e)
            kuntatinteSchemesList = []
        }
    }
    
    ColumnLayout {
        width: parent.width
        spacing: Kirigami.Units.smallSpacing
    
    // Header row
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Label {
            text: "Kuntatinte Scheme"
            font.bold: true
        }
        
        Item { Layout.fillWidth: true }
        
        Controls.ToolButton {
            icon.name: "view-refresh"
            Controls.ToolTip.text: "Regenerate preview"
            Controls.ToolTip.visible: hovered
            onClicked: updatePreview()
        }
    }
    
    SubtleSeparator {}   
    
    // Preview section
    // Collapsible Generation section (default expanded)
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        Controls.Label {
            text: "Generation"
            font.bold: true
            Layout.preferredWidth: 120
        }

        Item { Layout.fillWidth: true }

        Controls.ToolButton {
            id: generateToggle
            icon.name: generateExpanded ? "arrow-down" : "arrow-right"
            Controls.ToolTip.text: generateExpanded ? "Collapse" : "Expand"
            onClicked: generateExpanded = !generateExpanded
        }
    }

    ColumnLayout {
        visible: generateExpanded
        Layout.fillWidth: true
        
        // Info label
        Controls.Label {
            Layout.fillWidth: true
            text: "Generate Kuntatinte color schemes based in a primary color"
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            color: Kirigami.Theme.disabledTextColor
            wrapMode: Text.WordWrap
        }
        // Primary color selector
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Controls.Label {
                text: "Primary Colors:"
                font.bold: true
            }

            // Material You Accents section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                visible: root.sourceColors && root.sourceColors.length > 0

                Controls.Label {
                    text: "Material You (Accents):"
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 4

                    Repeater {
                        model: root.sourceColors

                        Rectangle {
                            property string myColor: modelData
                            width: 28
                            height: 28
                            radius: 4
                            color: myColor
                            border.width: (kdeSettings2.primaryColorIndex === -100 - index) ? 2 : 1
                            border.color: (kdeSettings2.primaryColorIndex === -100 - index)
                                ? Kirigami.Theme.highlightColor 
                                : Kirigami.Theme.disabledTextColor

                            Kirigami.Icon {
                                anchors.centerIn: parent
                                width: 14
                                height: 14
                                source: "dialog-ok"
                                color: kdeSettings2.getContrastTextColor(parent.myColor)
                                visible: kdeSettings2.primaryColorIndex === -100 - index
                            }

                            Controls.ToolTip.text: myColor
                            Controls.ToolTip.visible: sourceMouseArea.containsMouse

                            MouseArea {
                                id: sourceMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    kdeSettings2.primaryColorIndex = -100 - index
                                    updatePreview()
                                }
                            }
                        }
                    }
                }
            }

            // ImageMagick Accent section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                visible: root.extractedAccent && root.extractedAccent !== ""

                Controls.Label {
                    text: "ImageMagick (Accent):"
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    color: Kirigami.Theme.disabledTextColor
                }

                Rectangle {
                    width: 28
                    height: 28
                    radius: 4
                    color: root.extractedAccent
                    border.width: kdeSettings2.primaryColorIndex === -1 ? 2 : 1
                    border.color: kdeSettings2.primaryColorIndex === -1 
                        ? Kirigami.Theme.highlightColor 
                        : Kirigami.Theme.disabledTextColor

                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: 14
                        height: 14
                        source: "dialog-ok"
                        color: kdeSettings2.getContrastTextColor(root.extractedAccent)
                        visible: kdeSettings2.primaryColorIndex === -1
                    }

                    Controls.ToolTip.text: root.extractedAccent
                    Controls.ToolTip.visible: imAccentMouse.containsMouse

                    MouseArea {
                        id: imAccentMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            kdeSettings2.primaryColorIndex = -1
                            updatePreview()
                        }
                    }
                }
            }

            // Show message if no colors available
            Controls.Label {
                visible: root.extractedColors.length === 0 && root.sourceColorsCount === 0 && !root.extractedAccent
                text: "Extract a palette first"
                font.italic: true
                color: Kirigami.Theme.disabledTextColor
            }
        }

        SubtleSeparator {}

        // Toolbar opacity control
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Controls.Label {
                text: "Toolbar Opacity:"
            }

            Controls.SpinBox {
                id: opacitySpinBox
                from: 0
                to: 100
                value: kdeSettings2.toolbarOpacity
                stepSize: 5
                editable: true

                textFromValue: function(value) {
                    return value + "%"
                }

                valueFromText: function(text) {
                    return parseInt(text.replace("%", "")) || 0
                }

                onValueModified: kdeSettings2.toolbarOpacity = value
            }

            Item { Layout.fillWidth: true }
        }

        SubtleSeparator {}

        // Scheme variant selector
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Controls.Label {
                text: "Scheme Variant:"
            }

            Controls.Slider {
                id: schemeVariantSlider
                Layout.fillWidth: true
                from: 0
                to: 8
                stepSize: 1
                value: kdeSettings2.schemeVariant
                snapMode: Controls.Slider.SnapAlways

                onValueChanged: {
                    kdeSettings2.schemeVariant = value
                    backend.setConfigValue("color_scheme", "scheme_variant", value)
                    updatePreview()
                }
            }

            Controls.Label {
                text: schemeVariantsModel.get(schemeVariantSlider.value).text
                Layout.minimumWidth: Kirigami.Units.gridUnit * 6
                horizontalAlignment: Text.AlignHCenter
            }

            Item { Layout.fillWidth: true }
        }

        SubtleSeparator {}

        Controls.Label {
            text: "Preview"
            font.bold: true
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            color: Kirigami.Theme.disabledTextColor
        }

        // Previews side-by-side
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            // Dark theme preview
            Rectangle {
                id: darkPreview
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                color: previewData && previewData.dark && previewData.dark.window_bg ? previewData.dark.window_bg : "#1a1a1a"
                radius: 8
                border.width: 1
                border.color: previewData && previewData.dark && previewData.dark.button_bg ? previewData.dark.button_bg : "#333333"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: 4

                    Controls.Label {
                        text: "Kuntatinte Dark"
                        font.bold: true
                        color: previewData && previewData.dark && previewData.dark.window_fg ? previewData.dark.window_fg : "#ffffff"
                        font.pixelSize: 12
                    }

                    // Window background simulation
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: previewData && previewData.dark && previewData.dark.window_bg ? previewData.dark.window_bg : "#2a2a2a"
                        radius: 4

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 4

                            // Title bar simulation (using window colors)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 20
                                color: previewData.dark && previewData.dark.button_bg ? previewData.dark.button_bg : "#333333"
                                radius: 2

                                Controls.Label {
                                    anchors.centerIn: parent
                                    text: "Window Title"
                                    color: previewData.dark && previewData.dark.button_fg ? previewData.dark.button_fg : "#ffffff"
                                    font.pixelSize: 10
                                }
                            }

                            // Content area
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 4

                                // Text on view background (using view colors)
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    color: previewData.dark && previewData.dark.view_bg ? previewData.dark.view_bg : "#3a3a3a"
                                    radius: 2

                                    Controls.Label {
                                        anchors.centerIn: parent
                                        text: "Content text"
                                        color: previewData.dark && previewData.dark.view_fg ? previewData.dark.view_fg : "#cccccc"
                                        font.pixelSize: 9
                                    }
                                }

                                // Button simulations (normal and pressed states) - smaller and below content
                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 16
                                    spacing: 2

                                    // Normal button
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        color: previewData.dark && previewData.dark.button_bg ? previewData.dark.button_bg : "#8899aa"
                                        radius: 2

                                        Controls.Label {
                                            anchors.centerIn: parent
                                            text: "OK"
                                            color: previewData.dark && previewData.dark.button_fg ? previewData.dark.button_fg : "#000000"
                                            font.pixelSize: 6
                                            font.bold: true
                                        }
                                    }

                                    // Pressed/active button (using selection colors)
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        color: previewData.dark && previewData.dark.selection_bg ? previewData.dark.selection_bg : "#4a90e2"
                                        radius: 2

                                        Controls.Label {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: previewData.dark && previewData.dark.selection_fg ? previewData.dark.selection_fg : "#ffffff"
                                            font.pixelSize: 6
                                            font.bold: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Light theme preview
            Rectangle {
                id: lightPreview
                Layout.fillWidth: true
                Layout.preferredHeight: 120
                color: previewData && previewData.light && previewData.light.window_bg ? previewData.light.window_bg : "#f5f5f5"
                radius: 8
                border.width: 1
                border.color: previewData && previewData.light && previewData.light.button_bg ? previewData.light.button_bg : "#cccccc"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.smallSpacing
                    spacing: 4

                    Controls.Label {
                        text: "Kuntatinte Light"
                        font.bold: true
                        color: previewData && previewData.light && previewData.light.window_fg ? previewData.light.window_fg : "#000000"
                        font.pixelSize: 12
                    }

                    // Window background simulation
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: previewData.light && previewData.light.window_bg ? previewData.light.window_bg : "#e8e8e8"
                        radius: 4

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 6
                            spacing: 4

                            // Title bar simulation (using window colors)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 20
                                color: previewData.light && previewData.light.button_bg ? previewData.light.button_bg : "#d0d0d0"
                                radius: 2

                                Controls.Label {
                                    anchors.centerIn: parent
                                    text: "Window Title"
                                    color: previewData.light && previewData.light.button_fg ? previewData.light.button_fg : "#000000"
                                    font.pixelSize: 10
                                }
                            }

                            // Content area
                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 4

                                // Text on view background (using view colors)
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    color: previewData.light && previewData.light.view_bg ? previewData.light.view_bg : "#c8c8c8"
                                    radius: 2

                                    Controls.Label {
                                        anchors.centerIn: parent
                                        text: "Content text"
                                        color: previewData.light && previewData.light.view_fg ? previewData.light.view_fg : "#333333"
                                        font.pixelSize: 9
                                    }
                                }

                                // Button simulations (normal and pressed states) - smaller and below content
                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 16
                                    spacing: 2

                                    // Normal button
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        color: previewData.light && previewData.light.button_bg ? previewData.light.button_bg : "#667788"
                                        radius: 2

                                        Controls.Label {
                                            anchors.centerIn: parent
                                            text: "OK"
                                            color: previewData.light && previewData.light.button_fg ? previewData.light.button_fg : "#ffffff"
                                            font.pixelSize: 6
                                            font.bold: true
                                        }
                                    }

                                    // Pressed/active button (using selection colors)
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        color: previewData.light && previewData.light.selection_bg ? previewData.light.selection_bg : "#4a90e2"
                                        radius: 2

                                        Controls.Label {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: previewData.light && previewData.light.selection_fg ? previewData.light.selection_fg : "#ffffff"
                                            font.pixelSize: 6
                                            font.bold: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    
    // Action buttons (inside collapsible)
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        Controls.Button {
            Layout.fillWidth: true
            text: "Generate Both"
            icon.name: "document-save"
            enabled: root.extractedColors.length > 0 || root.sourceColorsCount > 0
            onClicked: {
                var selectedColor = kdeSettings2.getSelectedColor()
                var result = backend.generateKuntatinteSchemes(
                    root.extractedColors,
                    kdeSettings2.primaryColorIndex >= 0 ? kdeSettings2.primaryColorIndex : -1,
                    kdeSettings2.toolbarOpacity,
                    kdeSettings2.primaryColorIndex < 0 ? selectedColor : "",
                    schemeVariant
                )
                if (result === "") {
                    root.showPassiveNotification("Generated Kuntatinte Light and Dark")
                } else {
                    root.showPassiveNotification("Error: " + result)
                }
            }
        }
    }

    } // End inner ColumnLayout (collapsible)

    // Collapsible Edit section (default collapsed, empty for now)
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        Controls.Label {
            text: "Edit"
            font.bold: true
            Layout.preferredWidth: 120
        }

        Item { Layout.fillWidth: true }

        Controls.ToolButton {
            id: editToggle
            icon.name: editExpanded ? "arrow-down" : "arrow-right"
            Controls.ToolTip.text: editExpanded ? "Collapse" : "Expand"
            onClicked: {
                editExpanded = !editExpanded
                if (editExpanded) reloadKuntatinteSchemes()
            }
        }
    }

    ColumnLayout {
        visible: editExpanded
        Layout.fillWidth: true

        // Edit header + combobox for generated Kuntatinte schemes
        Controls.Label {
            text: "Edit Kuntatinte Schemes"
            font.bold: true
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            color: Kirigami.Theme.disabledTextColor
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Controls.ComboBox {
                id: kuntatinteCombo
                Layout.fillWidth: true
                model: kuntatinteSchemesList
                enabled: kuntatinteSchemesList.length > 0
                displayText: currentIndex >= 0 && model.length > 0 ? model[currentIndex] : "No Kuntatinte schemes"
                onActivated: {
                    // Fetch data synchronously from backend but delay assigning
                    // it to UI-bound properties until the next event loop tick.
                    var name = model[currentIndex]
                    editSchemeName = name

                    var data = {}
                    try {
                        data = backend.getFullSchemeData(name)
                    } catch (e) {
                        data = {}
                    }

                    var secs = []
                    try {
                        secs = backend.getColorSections(name)
                    } catch (e) {
                        var tmp = []
                        for (var k in data) tmp.push(k)
                        secs = tmp.sort()
                    }

                    var inactive = []
                    try {
                        inactive = backend.getInactiveSections(name)
                    } catch (e) {
                        inactive = []
                    }

                    // store in pending props and schedule actual assignment
                    kdeSettings2.pendingEditSchemeData = data
                    kdeSettings2.pendingEditSchemeSections = secs
                    kdeSettings2.pendingEditSchemeInactive = inactive
                    delayedAssignTimer.start()
                }
            }

            Controls.ToolButton {
                icon.name: "view-refresh"
                Controls.ToolTip.text: "Reload available schemes"
                Controls.ToolTip.visible: hovered
                onClicked: {
                    // Use the centralized reload function which also retrieves
                    // canonical section lists (and inactive-section info) from
                    // the backend. This prevents deriving duplicate section
                    // keys from the raw scheme data and therefore avoids
                    // creating separate tabs for Normal and Inactive.
                    reloadKuntatinteSchemes()
                }
            }

            // Quick save next to combo (same area as refresh)
            Controls.ToolButton {
                icon.name: "document-save"
                Controls.ToolTip.text: "Save scheme"
                Controls.ToolTip.visible: hovered
                enabled: editSchemeName !== ""
                onClicked: {
                    if (editSchemeName !== "") {
                        var isDark = editSchemeName.indexOf("Dark") !== -1
                        backend.saveKdeColorScheme(editSchemeName, isDark, editSchemeData)
                        root.kdeColorSchemesList = backend.getColorSchemesList()
                        root.showPassiveNotification("Saved: " + editSchemeName)
                    }
                }
            }

            Timer {
                id: delayedAssignTimer
                interval: 0
                repeat: false
                onTriggered: {
                    if (kdeSettings2.pendingEditSchemeData !== null) {
                        editSchemeData = kdeSettings2.pendingEditSchemeData
                        kdeSettings2.pendingEditSchemeData = null
                    }
                    if (kdeSettings2.pendingEditSchemeSections && kdeSettings2.pendingEditSchemeSections.length >= 0) {
                        editSchemeSections = kdeSettings2.pendingEditSchemeSections
                        kdeSettings2.pendingEditSchemeSections = []
                    }
                    if (kdeSettings2.pendingEditSchemeInactive && kdeSettings2.pendingEditSchemeInactive.length >= 0) {
                        editInactiveSections = kdeSettings2.pendingEditSchemeInactive
                        kdeSettings2.pendingEditSchemeInactive = []
                    }
                    console.log('delayedAssignTimer triggered: editSchemeSections.length=' + editSchemeSections.length + ', editInactiveSections.length=' + editInactiveSections.length)
                }
            }

            
        }

        // Editor container for the selected scheme
        ColumnLayout {
            id: editContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Kirigami.Units.smallSpacing
            clip: true

            // Tabs + content (sections)
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Kirigami.Units.smallSpacing

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40

                    Loader {
                        id: editTabBarLoader
                        anchors.fill: parent
                        active: editSchemeSections && editSchemeSections.length > 0
                        sourceComponent: active ? tabBarComponent : null
                    }
                }

                Component {
                    id: tabBarComponent
                    Controls.TabBar {
                        id: editTabBar
                        Layout.fillWidth: true

                        Repeater {
                            model: editSchemeSections
                            Controls.TabButton {
                                text: (function() {
                                    var section = modelData
                                    if (section && section.indexOf("Colors:") === 0) {
                                        return section.substring(7)
                                    }
                                    return section
                                })()
                            }
                        }
                    }
                }

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: editTabBarLoader.item !== undefined
                    currentIndex: editTabBarLoader.item ? editTabBarLoader.item.currentIndex : 0

                    Repeater {
                        model: editSchemeSections
                        Controls.ScrollView {
                            id: sectionScrollView
                            property string sectionName: modelData
                            property bool hasInactive: editInactiveSections.indexOf(sectionName) !== -1
                            property bool showInactive: false
                            property string activeSectionName: showInactive ? sectionName + "][Inactive" : sectionName
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            Controls.ScrollBar.horizontal.policy: Controls.ScrollBar.AlwaysOff
                            Controls.ScrollBar.vertical.policy: Controls.ScrollBar.AsNeeded

                            ColumnLayout {
                                width: availableWidth
                                spacing: Kirigami.Units.smallSpacing

                                // Normal/Inactive toggle (only if section has Inactive variant)
                                RowLayout {
                                    visible: sectionScrollView.hasInactive
                                    Layout.fillWidth: true
                                    Layout.bottomMargin: Kirigami.Units.smallSpacing

                                    Controls.Label {
                                        text: "State:"
                                        opacity: 0.7
                                    }

                                    Controls.Switch {
                                        checked: sectionScrollView.showInactive
                                        onCheckedChanged: sectionScrollView.showInactive = checked
                                    }

                                    Controls.Label {
                                        text: sectionScrollView.showInactive ? "Inactive" : "Normal"
                                        font.bold: true
                                    }

                                    Item { Layout.fillWidth: true }
                                }

                                Repeater {
                                    model: (function() {
                                        var sec = activeSectionName
                                        var data = editSchemeData[sec] || {}
                                        var keys = []
                                        for (var k in data) keys.push(k)
                                        return keys.sort()
                                    })()

                                    ColorRow {
                                        required property string modelData
                                        property string currentSection: activeSectionName
                                        label: modelData
                                        labelWidth: 140
                                        colorValue: {
                                            var d = editSchemeData[currentSection]
                                            return d && d[modelData] ? d[modelData].color : ""
                                        }
                                        colorOpacity: {
                                            var d = editSchemeData[currentSection]
                                            if (d && d[modelData] && d[modelData].opacity !== undefined) return Math.round(d[modelData].opacity*100)
                                            return 100
                                        }
                                        showOpacity: true

                                        onPaletteClicked: {
                                            if (root.selectedColor) {
                                                if (!editSchemeData[currentSection]) editSchemeData[currentSection] = {}
                                                editSchemeData[currentSection][modelData] = {color: root.selectedColor, opacity: colorOpacity/100}
                                                editSchemeData = JSON.parse(JSON.stringify(editSchemeData))
                                            }
                                        }
                                        onPickerColorSelected: function(color) {
                                            if (!editSchemeData[currentSection]) editSchemeData[currentSection] = {}
                                            editSchemeData[currentSection][modelData] = {color: color, opacity: colorOpacity/100}
                                            editSchemeData = JSON.parse(JSON.stringify(editSchemeData))
                                        }
                                        onOpacityModified: function(newOpacity) {
                                            if (!editSchemeData[currentSection]) editSchemeData[currentSection] = {}
                                            var cur = editSchemeData[currentSection][modelData] || {color: colorValue, opacity: newOpacity/100}
                                            cur.opacity = newOpacity/100
                                            editSchemeData[currentSection][modelData] = cur
                                            editSchemeData = JSON.parse(JSON.stringify(editSchemeData))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Apply buttons (outside collapsible)
    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        
        Controls.Button {
            Layout.fillWidth: true
            text: "Apply Dark"
            icon.name: "dialog-ok-apply"
            enabled: root.extractedColors.length > 0 || root.sourceColorsCount > 0
            onClicked: {
                var selectedColor = kdeSettings2.getSelectedColor()
                var genResult = backend.generateKuntatinteSchemes(
                    root.extractedColors,
                    kdeSettings2.primaryColorIndex >= 0 ? kdeSettings2.primaryColorIndex : -1,
                    kdeSettings2.toolbarOpacity,
                    kdeSettings2.primaryColorIndex < 0 ? selectedColor : "",
                    schemeVariant
                )
                if (genResult === "") {
                    if (backend.applyColorScheme("KuntatinteDark")) {
                        root.kdeCurrentScheme = "KuntatinteDark"
                        root.showPassiveNotification("Applied: Kuntatinte Dark")
                    }
                } else {
                    root.showPassiveNotification("Error: " + genResult)
                }
            }
        }
        
        Controls.Button {
            Layout.fillWidth: true
            text: "Apply Light"
            icon.name: "dialog-ok-apply"
            enabled: root.extractedColors.length > 0 || root.sourceColorsCount > 0
            onClicked: {
                var selectedColor = kdeSettings2.getSelectedColor()
                var genResult = backend.generateKuntatinteSchemes(
                    root.extractedColors,
                    kdeSettings2.primaryColorIndex >= 0 ? kdeSettings2.primaryColorIndex : -1,
                    kdeSettings2.toolbarOpacity,
                    kdeSettings2.primaryColorIndex < 0 ? selectedColor : "",
                    schemeVariant
                )
                if (genResult === "") {
                    if (backend.applyColorScheme("KuntatinteLight")) {
                        root.kdeCurrentScheme = "KuntatinteLight"
                        root.showPassiveNotification("Applied: Kuntatinte Light")
                    }
                } else {
                    root.showPassiveNotification("Error: " + genResult)
                }
            }
        }
    }

    // Spacer
    Item { Layout.fillHeight: true }

    } // End main ColumnLayout
}
