import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * SubtleSeparator - A subtle horizontal line separator.
 */
Item {
    Layout.fillWidth: true
    Layout.preferredHeight: 1
    Layout.topMargin: Kirigami.Units.smallSpacing
    Layout.bottomMargin: Kirigami.Units.smallSpacing
    
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
