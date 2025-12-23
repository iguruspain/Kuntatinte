import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import QtQuick.Window

/*
  AutogenDialog.qml

  Dialog component that shows the autogen JSON preview and allows saving
  the dump to a temp file via the backend. This keeps CentralPanel.qml
  clean and reusable.
*/

Window {
    id: rootDialog
    title: "Autogen Mode"
    width: 800
    height: 600
    visible: false
    color: Kirigami.Theme.backgroundColor

    // Preview data
    property string autogenText: ""
    property string autogenStatus: ""
    property string autogenPaletteMode: ""
    property var autogenGenerated: []

    // UI state
    property bool jsonPreviewExpanded: false
    property bool palettesMatch: false

    // Backend object must be set by the parent (CentralPanel)
    property var backend: null
    // Optional busy indicator from parent (passed as `busyIndicator: busyIndicator`)
    property var busyIndicator: null
    // Palette mode from parent
    property string paletteMode: "dark"
    // Selected image path from parent
    property string selectedImagePath: ""
    // Primary color from Kuntatinte Color Scheme
    property string primaryColor: ""
    // Accent color from central panel
    property string accentColor: ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        Controls.Label {
            text: "Generate autogen for current palette mode: <b><font color='" + (paletteMode === "dark" ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.linkColor) + "'>" + paletteMode.toUpperCase() + "</font></b>"
            textFormat: Text.RichText
        }

        ColumnLayout {
            spacing: Kirigami.Units.smallSpacing

            Controls.Button {
                text: "Generate (also colors)"
                Layout.fillWidth: true
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var res = backend.runAutogen(paletteMode, selectedImagePath, primaryColor, accentColor)
                        try {
                            var obj = JSON.parse(res)
                            rootDialog.autogenText = JSON.stringify(obj, null, 2)
                            rootDialog.autogenStatus = obj.status || ""
                            rootDialog.autogenPaletteMode = obj.palette_mode || ""
                            rootDialog.autogenGenerated = Object.keys(obj.generated || {})
                            jsonPreviewExpanded = true
                        } catch (e) {
                            rootDialog.autogenText = (res === undefined || res === null) ? "" : String(res)
                            rootDialog.autogenStatus = ""
                            rootDialog.autogenPaletteMode = ""
                            rootDialog.autogenGenerated = []
                            jsonPreviewExpanded = true
                        }
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }

            Controls.Button {
                text: "Generate (current colors)"
                Layout.fillWidth: true
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var res = backend.runAutogenCurrentColors(paletteMode, primaryColor, accentColor)
                        try {
                            var obj = JSON.parse(res)
                            rootDialog.autogenText = JSON.stringify(obj, null, 2)
                            rootDialog.autogenStatus = obj.status || ""
                            rootDialog.autogenPaletteMode = obj.palette_mode || ""
                            rootDialog.autogenGenerated = Object.keys(obj.generated || {})
                            jsonPreviewExpanded = true
                        } catch (e) {
                            rootDialog.autogenText = (res === undefined || res === null) ? "" : String(res)
                            rootDialog.autogenStatus = ""
                            rootDialog.autogenPaletteMode = ""
                            rootDialog.autogenGenerated = []
                            jsonPreviewExpanded = true
                        }
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }

            Controls.Button {
                text: "pywalpal"
                Layout.fillWidth: true
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var res = backend.runPywalPal(primaryColor, accentColor, selectedImagePath)
                        rootDialog.autogenText = (res === undefined || res === null) ? "" : String(res)
                        jsonPreviewExpanded = true
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }

            Controls.Button {
                text: "Compare" + (rootDialog.palettesMatch ? " ✓" : " ✗")
                Layout.fillWidth: true
                onClicked: {
                    rootDialog.palettesMatch = backend.comparePalettes()
                    rootDialog.autogenText = rootDialog.palettesMatch ? "Palettes match!" : "Palettes do not match. Check logs for details."
                    jsonPreviewExpanded = true
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            
            // Collapsible JSON Preview section (following app pattern)
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Controls.Label {
                    text: "JSON Preview"
                    font.bold: true
                    Layout.preferredWidth: 120
                }

                Item { Layout.fillWidth: true }

                Controls.ToolButton {
                    id: jsonPreviewToggle
                    icon.name: rootDialog.autogenText.length > 0 ? (jsonPreviewExpanded ? "arrow-down" : "arrow-right") : "arrow-right"
                    enabled: rootDialog.autogenText.length > 0
                    Controls.ToolTip.text: jsonPreviewExpanded ? "Collapse" : "Expand"
                    onClicked: {
                        jsonPreviewExpanded = !jsonPreviewExpanded
                    }
                }
            }
            
            // Container for ScrollView with copy button overlay
            Item {
                visible: jsonPreviewExpanded
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                
                Controls.ScrollView {
                    id: jsonScrollView
                    anchors.fill: parent
                    clip: true
                    
                    Controls.TextArea {
                        id: jsonTextArea
                        readOnly: true
                        wrapMode: Text.WrapAnywhere
                        text: rootDialog.autogenText
                        font.family: "monospace"
                    }
                }
                
                // Copy button positioned in top-right corner, next to scrollbar (not overlapping)
                Controls.ToolButton {
                    visible: rootDialog.autogenText.length > 0
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.rightMargin: 20 // Close to scrollbar but not overlapping
                    anchors.topMargin: Kirigami.Units.smallSpacing
                    icon.name: "edit-copy"
                    implicitWidth: 24
                    implicitHeight: 24
                    Controls.ToolTip.text: "Copy JSON to clipboard"
                    Controls.ToolTip.visible: hovered
                    onClicked: {
                        jsonTextArea.selectAll()
                        jsonTextArea.copy()
                        jsonTextArea.deselect()
                        root.showPassiveNotification("JSON copied to clipboard")
                    }
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: Kirigami.Units.smallSpacing

            Controls.Button {
                text: "Save JSON"
                enabled: rootDialog.autogenText.length > 0
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var ok = backend.saveAutogenDump(rootDialog.autogenText)
                    }
                    if (busyIndicator) busyIndicator.visible = false
                    rootDialog.close()
                }
            }

            Controls.Button {
                text: "Load values"
                enabled: rootDialog.autogenText.length > 0
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var ok = backend.applyAutogenColors(rootDialog.autogenText)
                        if (ok) {
                            root.showPassiveNotification("Autogen colors loaded to settings")
                        } else {
                            root.showPassiveNotification("Error loading autogen colors")
                        }
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }
        }

    }
}
