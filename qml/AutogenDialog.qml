import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/*
  AutogenDialog.qml

  Dialog component that shows the autogen JSON preview and allows saving
  the dump to a temp file via the backend. This keeps CentralPanel.qml
  clean and reusable.
*/

Controls.Dialog {
    id: rootDialog
    title: "Autogen Mode"
    modal: true
    standardButtons: Controls.Dialog.NoButton

    // Preview data
    property string autogenText: ""
    property string autogenStatus: ""
    property string autogenPaletteMode: ""
    property var autogenGenerated: []

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

    contentItem: ColumnLayout {
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        Controls.Label {
            text: "Generate autogen for current palette mode: <b><font color='" + (paletteMode === "dark" ? "#ff6b6b" : "#4ecdc4") + "'>" + paletteMode.toUpperCase() + "</font></b>"
            textFormat: Text.RichText
        }

        RowLayout {
            spacing: Kirigami.Units.smallSpacing

            Controls.Button {
                text: "Generate"
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
                        } catch (e) {
                            rootDialog.autogenText = (res === undefined || res === null) ? "" : String(res)
                            rootDialog.autogenStatus = ""
                            rootDialog.autogenPaletteMode = ""
                            rootDialog.autogenGenerated = []
                        }
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }
        }

        Controls.Label { text: "Autogen output (preview):" }

        RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Controls.Label { text: "Status: " + (rootDialog.autogenStatus || "-") }
            Controls.Label { text: "Mode: " + (rootDialog.autogenPaletteMode || "-") }
            Controls.Label { text: "Generated: " + (rootDialog.autogenGenerated.length > 0 ? rootDialog.autogenGenerated.join(", ") : "-") }
        }

        Controls.ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: 220
            Controls.TextArea {
                id: autogenOutput
                readOnly: true
                wrapMode: Text.WrapAnywhere
                text: rootDialog.autogenText
                font.family: "monospace"
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: Kirigami.Units.smallSpacing

            Controls.Button {
                text: "Save Dump"
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
                text: "Export"
                enabled: rootDialog.autogenText.length > 0
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var ok = backend.applyAutogenColors(rootDialog.autogenText)
                        if (ok) {
                            root.showPassiveNotification("Autogen colors exported to settings")
                        } else {
                            root.showPassiveNotification("Error exporting autogen colors")
                        }
                    }
                    if (busyIndicator) busyIndicator.visible = false
                }
            }

            Controls.Button {
                text: "Cancel"
                onClicked: rootDialog.close()
            }
        }
    }
}
