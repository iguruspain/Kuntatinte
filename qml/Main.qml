import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

/**
 * Main.qml - Main application window.
 * 
 * This file defines the application state and layout structure,
 * delegating panel content to separate component files.
 */
Kirigami.ApplicationWindow {
    id: root
    title: "Kuntatinte"
    height: 650
    width: 820
    
    // Minimum sizes from config
    readonly property int minCentralWidth: backend ? backend.getPanelWidth("central_panel") : 400
    readonly property int minWallpapersWidth: backend ? backend.getPanelWidth("wallpapers") : 250
    readonly property int minHeight: backend ? backend.getMinHeight() : 650
    
    // Absolute minimum is always the central panel - auto-collapse handles the rest
    minimumWidth: minCentralWidth
    minimumHeight: minHeight
    
    // Set initial width and load KDE colors
    Component.onCompleted: {
        loadKdeColors()
    }
    
    // =========================================================================
    // Application State Properties
    // =========================================================================
    
    // Extracted palette data
    property var extractedColors: []
    property var basePaletteColors: []  // Original palette before variant transformations
    property var paletteColors: extractedColors  // Alias for compatibility
    property string accentColor: extractedAccent  // Alias for compatibility
    property string extractedAccent: ""
    property var baseSourceColors: []  // Original source colors before variants
    property var sourceColors: []  // Material You source colors (with variants applied)
    property string selectedImagePath: ""
    property string wallpaperSource: "user"  // "user" or "system"
    
    // Material You source colors as individual properties (avoids QVariantList binding issues)
    property int sourceColorsCount: 0
    property string sourceColor0: ""
    property string sourceColor1: ""
    property string sourceColor2: ""
    property string sourceColor3: ""
    property string sourceColor4: ""
    property string sourceColor5: ""
    property string sourceColor6: ""
    
    function getSourceColor(idx) {
        switch(idx) {
            case 0: return sourceColor0
            case 1: return sourceColor1
            case 2: return sourceColor2
            case 3: return sourceColor3
            case 4: return sourceColor4
            case 5: return sourceColor5
            case 6: return sourceColor6
            default: return ""
        }
    }
    property int selectedSwatchIndex: -1
    property string extractionMethod: "ImageMagick"  // "ImageMagick", "Material You", "Pywal"
    property string paletteMode: "dark"  // "light", "dark"
    
    onPaletteModeChanged: {
        if (root.extractionMethod === "Material You" && root.sourceColors.length > 0) {
            var sliderPercent = 50.0
            var seedIndex = 0
            if (root.selectedSwatchIndex <= -101) seedIndex = -100 - root.selectedSwatchIndex
            backend.generateMaterialYouPaletteFromSeeds(root.sourceColors, root.paletteMode, seedIndex, sliderPercent)
        } else if (root.extractionMethod === "ImageMagick" && root.selectedImagePath !== "") {
            backend.extractColors(root.selectedImagePath, root.extractionMethod, root.paletteMode)
        }
    }
    
    // Starship accent colors
    property string selectedAccent: ""
    property string selectedAccentText: ""
    property string accentSource: ""      // "palette", "pick", or "loaded"
    property string accentTextSource: ""
    
    // Starship dir colors
    property string selectedDirFg: ""
    property string selectedDirBg: ""
    property string selectedDirText: ""
    property string dirFgSource: ""
    property string dirBgSource: ""
    property string dirTextSource: ""
    
    // Starship git colors
    property string selectedGitFg: ""
    property string selectedGitBg: ""
    property string selectedGitText: ""
    property string gitFgSource: ""
    property string gitBgSource: ""
    property string gitTextSource: ""
    
    // Starship other colors
    property string selectedOtherFg: ""
    property string selectedOtherBg: ""
    property string selectedOtherText: ""
    property string otherFgSource: ""
    property string otherBgSource: ""
    property string otherTextSource: ""
    
    // Fastfetch colors
    property string fastfetchAccent: ""
    property string fastfetchAccentSource: ""
    property string fastfetchLogoPath: ""  // Custom logo path
    property string fastfetchPreviewOriginal: ""  // Original logo preview URL
    property string fastfetchPreviewTinted: ""  // Tinted preview URL
    
    // OpenRGB colors
    property string openrgbAccent: ""
    property string openrgbAccentSource: ""
    
    // Ulauncher colors
    property string ulauncherBgColor: ""
    property int ulauncherBgOpacity: 100
    property string ulauncherBorderColor: ""
    property int ulauncherBorderOpacity: 100
    property string ulauncherPrefsBackground: ""
    property string ulauncherInputColor: ""
    property string ulauncherSelectedBgColor: ""
    property string ulauncherSelectedFgColor: ""
    property string ulauncherItemName: ""
    property string ulauncherItemText: ""
    property string ulauncherItemBoxSelected: ""
    property string ulauncherItemNameSelected: ""
    property string ulauncherItemTextSelected: ""
    property string ulauncherShortcutColor: ""
    property string ulauncherShortcutColorSel: ""
    property string ulauncherWhenSelected: ""
    property string ulauncherWhenNotSelected: ""
    
    // Ulauncher color sources
    property string ulauncherBgColorSource: ""
    property string ulauncherBorderColorSource: ""
    property string ulauncherPrefsBackgroundSource: ""
    property string ulauncherInputColorSource: ""
    property string ulauncherSelectedBgColorSource: ""
    property string ulauncherSelectedFgColorSource: ""
    property string ulauncherItemNameSource: ""
    property string ulauncherItemTextSource: ""
    property string ulauncherItemBoxSelectedSource: ""
    property string ulauncherItemNameSelectedSource: ""
    property string ulauncherItemTextSelectedSource: ""
    property string ulauncherShortcutColorSource: ""
    property string ulauncherShortcutColorSelSource: ""
    property string ulauncherWhenSelectedSource: ""
    property string ulauncherWhenNotSelectedSource: ""
    
    // KDE Color Scheme - Dynamic system
    property string kdeCurrentScheme: ""      // Currently applied system scheme
    property string kdeBaseScheme: ""         // Base scheme to derive colors from
    
    property var kdeColorSchemesList: []
    property var kdeColorSections: []         // List of color sections ["Colors:View", "Colors:Window", ...]
    property var kdeInactiveSections: []      // Sections that have Inactive variants ["Colors:Header"]
    property var kdeColorsData: ({})          // Full scheme data: {section: {key: {color, opacity}}}
    
    // =========================================================================
    // Computed Properties
    // =========================================================================
    
    // Currently selected color (from palette, extracted accent, or source colors)
    readonly property string selectedColor: {
        if (selectedSwatchIndex === -2 && extractedAccent !== "") {
            // ImageMagick recommended accent
            return extractedAccent
        } else if (selectedSwatchIndex <= -100) {
            // Material You source color: -100 = index 0, -101 = index 1, etc.
            var sourceIndex = -100 - selectedSwatchIndex
            if (sourceIndex < sourceColorsCount) {
                return getSourceColor(sourceIndex)
            }
        } else if (selectedSwatchIndex >= 0 && selectedSwatchIndex < extractedColors.length) {
            return extractedColors[selectedSwatchIndex]
        }
        return ""
    }
    
    // Indicates if there is a selected color (palette or accent)
    readonly property bool hasSelectedColor: selectedColor !== ""
    
    // =========================================================================
    // Color Reset Function
    // =========================================================================
    
    // Reset all settings colors when image changes (no auto-extraction)
    onSelectedImagePathChanged: resetSettingsColors()
    
    function resetSettingsColors() {
        // Reset extracted palette
        extractedColors = []
        basePaletteColors = []
        extractedAccent = ""
        baseSourceColors = []
        sourceColorsCount = 0
        sourceColor0 = ""
        sourceColor1 = ""
        sourceColor2 = ""
        sourceColor3 = ""
        sourceColor4 = ""
        sourceColor5 = ""
        sourceColor6 = ""
        selectedSwatchIndex = -1
        
        // Reset Starship colors
        selectedAccent = ""
        selectedAccentText = ""
        accentSource = ""
        accentTextSource = ""
        selectedDirFg = ""
        selectedDirBg = ""
        selectedDirText = ""
        dirFgSource = ""
        dirBgSource = ""
        dirTextSource = ""
        selectedGitFg = ""
        selectedGitBg = ""
        selectedGitText = ""
        gitFgSource = ""
        gitBgSource = ""
        gitTextSource = ""
        selectedOtherFg = ""
        selectedOtherBg = ""
        selectedOtherText = ""
        otherFgSource = ""
        otherBgSource = ""
        otherTextSource = ""
        
        // Reset Fastfetch colors (keep logo path, reset accent and preview)
        fastfetchAccent = ""
        fastfetchAccentSource = ""
        fastfetchPreviewTinted = ""
        
        // Reset Ulauncher colors
        ulauncherBgColor = ""
        ulauncherBorderColor = ""
        ulauncherPrefsBackground = ""
        ulauncherInputColor = ""
        ulauncherSelectedBgColor = ""
        ulauncherSelectedFgColor = ""
        ulauncherItemName = ""
        ulauncherItemText = ""
        ulauncherItemBoxSelected = ""
        ulauncherItemNameSelected = ""
        ulauncherItemTextSelected = ""
        ulauncherShortcutColor = ""
        ulauncherShortcutColorSel = ""
        ulauncherWhenSelected = ""
        ulauncherWhenNotSelected = ""
        ulauncherBgColorSource = ""
        ulauncherBorderColorSource = ""
        ulauncherPrefsBackgroundSource = ""
        ulauncherInputColorSource = ""
        ulauncherSelectedBgColorSource = ""
        ulauncherSelectedFgColorSource = ""
        ulauncherItemNameSource = ""
        ulauncherItemTextSource = ""
        ulauncherItemBoxSelectedSource = ""
        ulauncherItemNameSelectedSource = ""
        ulauncherItemTextSelectedSource = ""
        ulauncherShortcutColorSource = ""
        ulauncherShortcutColorSelSource = ""
        ulauncherWhenSelectedSource = ""
        ulauncherWhenNotSelectedSource = ""
    }

    // Reset only the palette-related UI state (keeps other settings intact)
    function resetPaletteState() {
        extractedColors = []
        basePaletteColors = []
        extractedAccent = ""
        baseSourceColors = []
        sourceColors = []
        sourceColorsCount = 0
        sourceColor0 = ""
        sourceColor1 = ""
        sourceColor2 = ""
        sourceColor3 = ""
        sourceColor4 = ""
        sourceColor5 = ""
        sourceColor6 = ""
        selectedSwatchIndex = -1
    }
    
    // =========================================================================
    // KDE Color Scheme Functions
    // =========================================================================
    
    function loadKdeColors() {
        kdeCurrentScheme = backend.getCurrentColorScheme()
        kdeColorSchemesList = backend.getColorSchemesList()
        
        // Set base scheme to current if not already set
        if (!kdeBaseScheme) {
            kdeBaseScheme = kdeCurrentScheme
        }
        
        // Load colors from base scheme
        loadKdeColorsFromScheme(kdeBaseScheme)
    }
    
    function loadKdeColorsFromScheme(schemeName) {
        if (!schemeName) return
        
        // Get color sections dynamically (main sections only)  
        kdeColorSections = backend.getColorSections(schemeName)
        
        // Get which sections have Inactive variants
        kdeInactiveSections = backend.getInactiveSections(schemeName)
        
        // Load full scheme data (includes Inactive sections too)
        kdeColorsData = backend.getFullSchemeData(schemeName)
        
        console.log("Loaded scheme:", schemeName, "with sections:", kdeColorSections.length, "inactive:", kdeInactiveSections.length)
    }
    
    function updateKdeColor(section, key, color, opacity) {
        // Create a deep copy to force binding update
        var newData = JSON.parse(JSON.stringify(kdeColorsData))
        
        if (!newData[section]) {
            newData[section] = {}
        }
        newData[section][key] = {
            "color": color,
            "opacity": opacity !== undefined ? opacity : 1.0
        }
        
        // Assign new object to trigger bindings
        kdeColorsData = newData
    }
    
     /* Removed deprecated KDE mode properties and save/apply helpers
         These were residual (kdeIsDarkMode/kdeTargetScheme) and
         the Kuntatinte generator uses explicit Apply Dark/Light actions.
     */
    
    // =========================================================================
    // UI State Properties
    // =========================================================================
    
    // Panel visibility - single source of truth
    property bool leftPanelVisible: true
    property bool rightPanelVisible: false  // Hidden by default
    property int currentSettingsIndex: 0  // Track which settings panel is active
    property string currentSettingName: ""  // Track current setting by name
    
    // Flag to prevent window resize during auto-collapse/expand
    property bool isAutoCollapsing: false
    
    // Current settings panel width
    readonly property int currentSettingsPanelWidth: backend ? backend.getPanelWidth(currentSettingName) : 280
    readonly property int separatorWidth: 1
    
    // =========================================================================
    // Debug UI Logging
    // =========================================================================
    
    // Helper function for conditional UI logging
    function logUI(message) {
        if (backend && backend.debugUi) {
            console.log("[UI] " + message)
        }
    }
    
    // =========================================================================
    // Window Management - Responsive Auto-collapse
    // =========================================================================
    
    // React to window width changes
    onWidthChanged: {
        logUI("Window width changed to: " + root.width)
        checkAutoCollapse()
    }
    
    function setInitialWindowSize() {
        // Calculate initial width based on visible panels
        var initialWidth = minCentralWidth
        if (leftPanelVisible) {
            initialWidth += minWallpapersWidth + separatorWidth
        }
        if (rightPanelVisible && backend) {
            initialWidth += currentSettingsPanelWidth + separatorWidth
        }
        logUI("setInitialWindowSize: " + initialWidth)
        root.width = initialWidth
    }
    
    function checkAutoCollapse() {
        // Skip if we're already in an auto-collapse operation
        if (isAutoCollapsing) {
            logUI("checkAutoCollapse: SKIPPED (isAutoCollapsing=true)")
            return
        }
        
        var availableWidth = root.width
        var centralMin = minCentralWidth
        var wallpapersMin = minWallpapersWidth + separatorWidth
        var settingsMin = currentSettingsPanelWidth + separatorWidth
        
        // Calculate space needed for visible panels
        var spaceNeeded = centralMin
        if (leftPanelVisible) spaceNeeded += wallpapersMin
        if (rightPanelVisible) spaceNeeded += settingsMin
        
        logUI("checkAutoCollapse: available=" + availableWidth + 
              " needed=" + spaceNeeded +
              " leftVisible=" + leftPanelVisible +
              " rightVisible=" + rightPanelVisible)
        
        // If we don't have enough space, hide panels (Settings first, then Wallpapers)
        if (availableWidth < spaceNeeded) {
            isAutoCollapsing = true  // Prevent window resize in onVisibleChanged
            
            // Try hiding Settings first
            if (rightPanelVisible && availableWidth < spaceNeeded) {
                logUI(">>> AUTO-HIDE Settings panel")
                rightPanelVisible = false
                spaceNeeded -= settingsMin
            }
            // If still not enough, hide Wallpapers
            if (leftPanelVisible && availableWidth < spaceNeeded) {
                logUI(">>> AUTO-HIDE Wallpapers panel")
                leftPanelVisible = false
            }
            
            isAutoCollapsing = false
        }
    }
    
    // When user toggles panels via button, adjust window size
    onLeftPanelVisibleChanged: {
        logUI("leftPanelVisible changed to: " + leftPanelVisible + " isAutoCollapsing: " + isAutoCollapsing)
        
        // Only resize window if user clicked the button (not auto-collapse)
        if (!isAutoCollapsing) {
            if (leftPanelVisible) {
                logUI("Expanding window for left panel: " + root.width + " + " + (minWallpapersWidth + separatorWidth))
                root.width = root.width + minWallpapersWidth + separatorWidth
            } else {
                logUI("Shrinking window for left panel: " + root.width + " - " + (minWallpapersWidth + separatorWidth))
                root.width = root.width - minWallpapersWidth - separatorWidth
            }
        }
    }
    
    onRightPanelVisibleChanged: {
        logUI("rightPanelVisible changed to: " + rightPanelVisible + " isAutoCollapsing: " + isAutoCollapsing)
        
        // Only resize window if user clicked the button (not auto-collapse)
        if (!isAutoCollapsing) {
            if (rightPanelVisible) {
                logUI("Expanding window for right panel: " + root.width + " + " + (currentSettingsPanelWidth + separatorWidth))
                root.width = root.width + currentSettingsPanelWidth + separatorWidth
            } else {
                logUI("Shrinking window for right panel: " + root.width + " - " + (currentSettingsPanelWidth + separatorWidth))
                root.width = root.width - currentSettingsPanelWidth - separatorWidth
            }
        }
    }
    
    // Track previous settings panel width for smooth transitions
    property int previousSettingsPanelWidth: 280  // Default starting value
    
    onCurrentSettingNameChanged: {
        // Get new panel width
        var newPanelWidth = backend ? backend.getPanelWidth(currentSettingName) : 280
        
        logUI("currentSettingName changed to: " + currentSettingName + 
              " newPanelWidth: " + newPanelWidth +
              " previousWidth: " + previousSettingsPanelWidth +
              " rightPanelVisible: " + rightPanelVisible)
        
        if (rightPanelVisible) {
            // Calculate the width difference between old and new panel
            var widthDiff = newPanelWidth - previousSettingsPanelWidth
            logUI("Panel resize: " + previousSettingsPanelWidth + " -> " + newPanelWidth + " diff: " + widthDiff)
            logUI("Window resize: " + root.width + " + " + widthDiff + " = " + (root.width + widthDiff))
            
            // Temporarily disable auto-collapse during resize
            isAutoCollapsing = true
            root.width = root.width + widthDiff
            isAutoCollapsing = false
            logUI("After resize: window.width=" + root.width)
        }
        // Update previous width for next change
        previousSettingsPanelWidth = newPanelWidth
    }
    
    function calculateMinWidthForCurrentState() {
        var minWidth = minCentralWidth
        if (leftPanelVisible) {
            minWidth += minWallpapersWidth + separatorWidth
        }
        if (rightPanelVisible && backend) {
            minWidth += currentSettingsPanelWidth + separatorWidth
        }
        return minWidth
    }

    // =========================================================================
    // Main Page Layout
    // =========================================================================
    
    // Main page without duplicate header
    pageStack.initialPage: Kirigami.Page {
        id: mainPage
        title: ""
        globalToolBarStyle: Kirigami.ApplicationHeaderStyle.None
        
        RowLayout {
            anchors.fill: parent
            spacing: 0
            
            // Left panel: Wallpapers sidebar
            WallpapersPanel {
                id: wallpapersPanel
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 20
                Layout.bottomMargin: 20
            }
            
            // Left vertical separator
            Rectangle {
                visible: root.leftPanelVisible
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                Layout.topMargin: 20
                Layout.bottomMargin: 20
                color: Kirigami.Theme.textColor
                opacity: 0.15
            }
            
            // Central panel: Preview and palette (fills remaining space)
            CentralPanel {
                id: centralPanel
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 20
                Layout.bottomMargin: 20
            }
            
            // Right vertical separator
            Rectangle {
                visible: root.rightPanelVisible
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                Layout.topMargin: 20
                Layout.bottomMargin: 20
                color: Kirigami.Theme.textColor
                opacity: 0.15
            }
            
            // Right panel: Settings
            SettingsPanel {
                id: settingsPanel
                visible: root.rightPanelVisible
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 20
                Layout.bottomMargin: 20
                Layout.preferredWidth: visible ? root.currentSettingsPanelWidth : 0
                Layout.minimumWidth: visible ? root.currentSettingsPanelWidth : 0
                Layout.maximumWidth: visible ? root.currentSettingsPanelWidth : 0
            }
        }
    }
    
    // =========================================================================
    // Backend Connections
    // =========================================================================
    
    Connections {
        target: backend
        
        function onColorsExtracted(colors) {
            // Store the base palette
            root.basePaletteColors = colors
            root.extractedColors = colors
            centralPanel.hideBusyIndicator()
        }
        
        function onAccentExtracted(color) {
            root.extractedAccent = color
            centralPanel.hideBusyIndicator()
        }
        
        function onSourceColorsExtracted(colorsJson) {
            // Parse JSON string to array
            var colors = JSON.parse(colorsJson)
            
            root.baseSourceColors = colors
            // Keep `sourceColors` equal to the original extracted seeds (do not
            // apply tonal variants to accents). The tonal slider will not
            // modify these accent swatches.
            root.sourceColors = colors
            root.sourceColorsCount = colors.length
            
            // Also update individual source color properties for getSourceColor()
            root.sourceColor0 = colors.length > 0 ? colors[0] : ""
            root.sourceColor1 = colors.length > 1 ? colors[1] : ""
            root.sourceColor2 = colors.length > 2 ? colors[2] : ""
            root.sourceColor3 = colors.length > 3 ? colors[3] : ""
            root.sourceColor4 = colors.length > 4 ? colors[4] : ""
            root.sourceColor5 = colors.length > 5 ? colors[5] : ""
            root.sourceColor6 = colors.length > 6 ? colors[6] : ""
            
            // Set default selected acento to the first one if not already set to a valid source color
            if (root.selectedSwatchIndex < -100 || root.selectedSwatchIndex > -100 - colors.length) {
                root.selectedSwatchIndex = -100  // First accent (Material You #1)
            }
            
            // Note: do NOT apply tonal variants to `sourceColors` (recommended accents).
            // The main palette (`extractedColors`) is the only thing variant-applied.

            // If we're in Material You mode, trigger palette generation now
            if (root.extractionMethod === "Material You" && backend && backend.isMaterialYouAvailable()) {
                var sliderPercent = 50.0
                var seedIndex = 0
                if (root.selectedSwatchIndex <= -101) seedIndex = -100 - root.selectedSwatchIndex
                var mode = root.paletteMode
                // Use seeds we just received to generate palette without backend caches
                backend.generateMaterialYouPaletteFromSeeds(colors, mode, seedIndex, sliderPercent)
            }

            centralPanel.hideBusyIndicator()
        }
        
        function onExtractionError(error) {
            centralPanel.hideBusyIndicator()
            showPassiveNotification("Error: " + error)
        }
        
        function onImageListChanged() {
            // The list updates automatically via property binding
        }
    }
}
