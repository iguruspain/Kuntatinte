import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * ColorRow - Reusable color selection row with swatch, picker, and palette button.
 * Supports optional opacity control via showOpacity property.
 */
RowLayout {
    id: colorRow
    Layout.fillWidth: true
    spacing: Kirigami.Units.smallSpacing
    
    required property string label
    required property string colorValue
    property string colorSource: ""
    property int colorOpacity: 100  // int 0-100 for SpinBox
    property bool showOpacity: false
    property int labelWidth: 120  // Fixed label width for alignment
    
    signal paletteClicked()
    signal pickerColorSelected(string color)
    signal opacityModified(int newOpacity)
    
    // Label - fixed width for alignment
    Controls.Label {
        text: colorRow.label
        Layout.preferredWidth: colorRow.labelWidth
        Layout.minimumWidth: colorRow.labelWidth
        elide: Text.ElideRight
    }
    
    // Spacer to push controls to the right
    Item { Layout.fillWidth: true }
    
    // Color swatch - fixed size
    Rectangle {
        Layout.preferredWidth: 32
        Layout.preferredHeight: 22
        color: colorRow.colorValue || "transparent"
        opacity: colorRow.colorOpacity / 100.0
        border.color: Kirigami.Theme.disabledTextColor
        border.width: 1
        radius: 2
        
        Controls.ToolTip.text: colorRow.colorValue + (colorRow.showOpacity ? " (" + colorRow.colorOpacity + "%)" : "")
        Controls.ToolTip.visible: swatchMouse.containsMouse && colorRow.colorValue
        
        MouseArea {
            id: swatchMouse
            anchors.fill: parent
            hoverEnabled: true
        }
    }
    
    // Opacity control - only shown when needed
    Controls.SpinBox {
        visible: colorRow.showOpacity
        Layout.preferredWidth: 55
        Layout.maximumWidth: 60
        from: 0
        to: 100
        value: colorRow.colorOpacity
        stepSize: 1
        editable: true
        
        textFromValue: function(value) { return value.toString() }
        valueFromText: function(text) { return parseInt(text) }
        
        onValueModified: {
            colorRow.opacityModified(value)
        }
    }
    
    // Color picker button - fixed size
    Controls.ToolButton {
        icon.name: "color-picker"
        implicitWidth: 28
        implicitHeight: 28
        Controls.ToolTip.text: "Pick color"
        Controls.ToolTip.visible: hovered
        onClicked: {
            var c = backend.pickColor(colorRow.colorValue || "")
            if (c) {
                colorRow.pickerColorSelected(c)
            }
        }
    }
    
    // Palette button - fixed size
    Controls.ToolButton {
        icon.name: "palette-symbolic"
        implicitWidth: 28
        implicitHeight: 28
        enabled: root.hasSelectedColor
        highlighted: colorRow.colorSource === "palette"
        Controls.ToolTip.text: "Use palette color"
        Controls.ToolTip.visible: hovered
        onClicked: colorRow.paletteClicked()
    }
}
