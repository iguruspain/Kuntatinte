import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "settings" as Settings

/**
 * SettingsPanel - Right sidebar with modular settings configuration.
 * Uses a ComboBox in the header to switch between different settings views.
 * Each settings module is in its own QML file under settings/
 * 
 * Shared components (ColorRow, SubtleSeparator) are in the settings/ module.
 */
Rectangle {
    id: settingsPanel
    
    visible: root.rightPanelVisible
    Layout.fillHeight: true
    Layout.preferredWidth: backend ? backend.getPanelWidth(currentSettingName) : 280
    color: Kirigami.Theme.backgroundColor
    
    // Current settings view by name instead of index
    property int currentSettingsIndex: 0
    property string currentSettingName: availableSettings.length > 0 ? availableSettings[currentSettingsIndex] : ""
    property var availableSettings: []
    
    // Load available settings on component creation
    Component.onCompleted: {
        availableSettings = backend.getAvailableSettings()
    }
    
    // Sync with root to update window width
    onCurrentSettingNameChanged: {
        root.currentSettingsIndex = currentSettingsIndex
        // Also sync the name for window width calculation
        root.currentSettingName = currentSettingName
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Panel header - simplified (just title and selector)
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
                    text: "Settings"
                    level: 2
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                }
                
                Controls.ComboBox {
                    id: settingsComboBox
                    model: settingsPanel.availableSettings
                    currentIndex: settingsPanel.currentSettingsIndex
                    onCurrentIndexChanged: settingsPanel.currentSettingsIndex = currentIndex
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
        
        // Settings content area with StackLayout
        StackLayout {
            id: settingsStackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing
            
            currentIndex: {
                switch(settingsPanel.currentSettingName) {
                    case "Fastfetch": return 0
                    case "Starship": return 1
                    case "Ulauncher": return 2
                    case "Kuntatinte Color Scheme": return 3
                    default: return 0
                }
            }
            
            // Modular settings components
            Settings.FastfetchSettings {}
            Settings.StarshipSettings {}
            Settings.UlauncherSettings {}
            Settings.KuntatinteColorSchemeSettings {}
        }
    }
}
