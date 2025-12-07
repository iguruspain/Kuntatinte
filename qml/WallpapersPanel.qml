import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * WallpapersPanel - Left sidebar displaying image thumbnails.
 * 
 * Required properties from parent:
 * - root.leftPanelVisible: bool
 * - root.selectedImagePath: string
 * - root.extractedColors: array
 * - root.extractedAccent: string
 * - root.selectedSwatchIndex: int
 * - root.selectedAccent: string
 * - root.selectedAccentText: string
 * - root.accentSource: string
 * - root.accentTextSource: string
 * - root.fastfetchAccent: string
 * - root.fastfetchAccentSource: string
 * - root.selectedDirFg/Bg/Text: string
 * - root.selectedGitFg/Bg/Text: string
 * - root.selectedOtherFg/Bg/Text: string
 * - root.dirFgSource/BgSource/TextSource: string
 * - root.gitFgSource/BgSource/TextSource: string
 * - root.otherFgSource/BgSource/TextSource: string
 * - backend: PaletteBackend
 */
Rectangle {
    id: wallpapersPanel
    
    visible: root.leftPanelVisible
    Layout.fillHeight: true
    Layout.fillWidth: false  // Don't compete with central panel
    Layout.minimumWidth: visible ? root.minWallpapersWidth : 0
    Layout.maximumWidth: visible ? 400 : 0  // Don't grow too large
    Layout.preferredWidth: visible ? root.minWallpapersWidth : 0
    color: Kirigami.Theme.backgroundColor
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
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
                
                Kirigami.Heading {
                    text: "Wallpapers"
                    level: 2
                    Layout.alignment: Qt.AlignVCenter
                }
                
                Item {
                    Layout.fillWidth: true
                }
                
                Controls.ComboBox {
                    model: ["Custom", "Default"]
                    currentIndex: root.wallpaperSource === "user" ? 0 : 1
                    onCurrentTextChanged: root.wallpaperSource = currentText === "Custom" ? "user" : "system"
                    Layout.alignment: Qt.AlignVCenter
                }
                
                Controls.ToolButton {
                    icon.name: "folder-open"
                    onClicked: backend.openFolderDialog()
                    Controls.ToolTip.text: "Browse Folder"
                    Controls.ToolTip.visible: hovered
                    opacity: root.wallpaperSource === "user" ? 1 : 0
                    enabled: root.wallpaperSource === "user"
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: -Kirigami.Units.largeSpacing
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
        
        // Thumbnail grid
        Controls.ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            background: Item {}
            
            GridView {
                id: thumbnailGrid
                
                // Calculate how many columns fit (minimum 100px per thumbnail)
                readonly property int columns: Math.max(2, Math.floor(width / 100))
                readonly property real cellSize: width / columns
                
                cellWidth: cellSize
                cellHeight: cellSize * 0.75
                clip: true
                
                model: backend ? (root.wallpaperSource === "user" ? backend.imageList : backend.systemImageList) : []
                
                delegate: Item {
                    width: thumbnailGrid.cellWidth
                    height: thumbnailGrid.cellHeight
                    
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 4
                        color: "transparent"
                        border.color: modelData === root.selectedImagePath ? 
                            Kirigami.Theme.highlightColor : "transparent"
                        border.width: 3
                        radius: 6
                        
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 2
                            radius: 4
                            clip: true
                            color: Kirigami.Theme.alternateBackgroundColor
                            
                            Image {
                                anchors.fill: parent
                                source: "file://" + modelData
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                
                                Controls.BusyIndicator {
                                    anchors.centerIn: parent
                                    running: parent.status === Image.Loading
                                    visible: running
                                }
                            }
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                root.selectedImagePath = modelData
                            }
                        }
                    }
                }
            }
        }
    }
}
