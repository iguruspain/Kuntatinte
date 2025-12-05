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

    contentItem: ColumnLayout {
        Layout.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        Controls.Label { text: "Choose palette mode to generate:" }

        RowLayout {
            spacing: Kirigami.Units.smallSpacing

            Controls.Button {
                text: "Dark"
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var res = backend.runAutogen("dark")
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

            Controls.Button {
                text: "Light"
                onClicked: {
                    if (busyIndicator) busyIndicator.visible = true
                    if (backend) {
                        var res = backend.runAutogen("light")
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

            Controls.Button { text: "Cancel"; onClicked: rootDialog.close() }
        }

        Controls.Label { text: "Autogen output (preview):" }

        RowLayout {
            spacing: Kirigami.Units.smallSpacing
            Controls.Label { text: "Status: " + (rootDialog.autogenStatus || "-") }
            Controls.Label { text: "Mode: " + (rootDialog.autogenPaletteMode || "-") }
            Controls.Label { text: "Generated: " + (rootDialog.autogenGenerated.length > 0 ? rootDialog.autogenGenerated.join(", ") : "-") }
        }

        Controls.TextArea {
            id: autogenOutput
            readOnly: true
            wrapMode: Text.WrapAnywhere
            text: rootDialog.autogenText
            font.family: "monospace"
            Layout.preferredHeight: 220
            Layout.fillWidth: true
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

            Controls.Button { text: "Close"; onClicked: rootDialog.close() }
        }
    }
}
