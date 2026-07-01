import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: root; visible: true
    width: 1280; height: 800
    minimumWidth: 1024; minimumHeight: 680
    title: "VisionFlow | 视觉智能筛选系统"

    readonly property color cBgStart:     "#FCF7F0"
    readonly property color cBgEnd:       "#F0E9E0"
    readonly property color cCardBg:      Qt.rgba(245/255, 252/255, 248/255, 0.65)
    readonly property color cCardBorder:  Qt.rgba(100/255, 116/255, 139/255, 0.20)
    readonly property color cCyan:        "#2563EB"
    readonly property color cGreen:       "#059669"
    readonly property color cGold:        "#D97706"
    readonly property color cTextWhite:   "#1E3A5F"
    readonly property color cTextSec:     "#5A7184"
    readonly property color cTextDim:     "#94A3B8"
    readonly property color cGlowSoft:    Qt.rgba(37/255, 99/255, 235/255, 0.10)
    readonly property color cGlowPurple:  Qt.rgba(37/255, 99/255, 235/255, 0.15)
    readonly property color cPurple:      "#2563EB"
    readonly property int   cRadius:      12
    readonly property int   cRadiusSm:    8
    property int currentPage: 0
    property int workMode: 1 // 0=直接选择, 1=智能匹配
    ListModel { id: screwListModel }
    function loadScrewList() {
        screwListModel.clear();
        var list = backend.getScrewListForQml();
        for (var i = 0; i < list.length; i++) {
            screwListModel.append(list[i]);
        }
        if (list.length > 0) {
            backend.selectScrew(list[0].id)
        }
    }
    Component.onCompleted: loadScrewList()
    Connections { target: backend; onScrewListChanged: loadScrewList() }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: cBgStart }
            GradientStop { position: 1.0; color: cBgEnd }
        }
    }
    Canvas {
        anchors.fill: parent; opacity: 0.06
        onPaint: {
            var ctx = getContext("2d");
            ctx.strokeStyle = Qt.rgba(100/255,116/255,139/255,0.3);
            ctx.lineWidth = 0.5; var step = 64;
            for (var x = step; x < width; x += step) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
            }
            for (var y = step; y < height; y += step) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
            }
        }
    }
    Canvas {
        id: glowCanvas; anchors.fill: parent; antialiasing: true
        property real p1: 0.0; property real p2: 2.0; property real p3: 4.0
        onPaint: {
            var ctx = getContext("2d");
            var w = width, h = height;
            ctx.clearRect(0, 0, w, h);
            var cx1 = w * (0.05 + 0.85 * (0.5 + 0.5 * Math.sin(p1)));
            var cy1 = h * (0.10 + 0.75 * (0.5 + 0.5 * Math.cos(p1 * 0.8)));
            var g1 = ctx.createRadialGradient(cx1, cy1, 0, cx1, cy1, w * 0.38);
            g1.addColorStop(0, "rgba(37, 99, 235, 0.45)");
            g1.addColorStop(0.4, "rgba(37, 99, 235, 0.20)");
            g1.addColorStop(0.7, "rgba(37, 99, 235, 0.05)");
            g1.addColorStop(1, "rgba(37, 99, 235, 0)");
            ctx.fillStyle = g1; ctx.fillRect(0, 0, w, h);
            var cx2 = w * (0.10 + 0.75 * (0.5 + 0.5 * Math.sin(p2)));
            var cy2 = h * (0.05 + 0.85 * (0.5 + 0.5 * Math.cos(p2 * 0.9)));
            var g2 = ctx.createRadialGradient(cx2, cy2, 0, cx2, cy2, w * 0.38);
            g2.addColorStop(0, "rgba(245, 158, 11, 0.40)");
            g2.addColorStop(0.4, "rgba(245, 158, 11, 0.18)");
            g2.addColorStop(0.7, "rgba(245, 158, 11, 0.05)");
            g2.addColorStop(1, "rgba(245, 158, 11, 0)");
            ctx.fillStyle = g2; ctx.fillRect(0, 0, w, h);
            var cx3 = w * (0.05 + 0.85 * (0.5 + 0.5 * Math.sin(p3)));
            var cy3 = h * (0.10 + 0.80 * (0.5 + 0.5 * Math.cos(p3 * 1.1)));
            var g3 = ctx.createRadialGradient(cx3, cy3, 0, cx3, cy3, w * 0.32);
            g3.addColorStop(0, "rgba(8, 145, 178, 0.40)");
            g3.addColorStop(0.4, "rgba(8, 145, 178, 0.18)");
            g3.addColorStop(0.7, "rgba(8, 145, 178, 0.05)");
            g3.addColorStop(1, "rgba(8, 145, 178, 0)");
            ctx.fillStyle = g3; ctx.fillRect(0, 0, w, h);
            // Fixed warm light source — bottom-left
            var cx4 = w * 0.12;
            var cy4 = h * 0.82;
            var g4 = ctx.createRadialGradient(cx4, cy4, 0, cx4, cy4, w * 0.22);
            g4.addColorStop(0, "rgba(59, 130, 246, 0.25)");
            g4.addColorStop(0.5, "rgba(59, 130, 246, 0.12)");
            g4.addColorStop(1, "rgba(59, 130, 246, 0)");
            ctx.fillStyle = g4; ctx.fillRect(0, 0, w, h);
        }
        Timer {
            interval: 50; running: true; repeat: true
            onTriggered: {
                glowCanvas.p1 += 0.045; glowCanvas.p2 += 0.045; glowCanvas.p3 += 0.055;
                glowCanvas.requestPaint();
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 14
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 48; radius: cRadiusSm
            color: Qt.rgba(232/255,248/255,238/255,0.55)
            border.color: Qt.rgba(100/255,116/255,139/255,0.12); border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                Row { spacing: 10
                    Rectangle { width: 8; height: 8; radius: 4; color: cCyan; anchors.verticalCenter: parent.verticalCenter
                        SequentialAnimation on opacity { loops: Animation.Infinite
                            PropertyAnimation { to: 0.3; duration: 1200 }
                            PropertyAnimation { to: 1.0; duration: 1200 } } }
                    Text { text: "VisionFlow"; font.pixelSize: 15; font.weight: Font.Bold; color: cCyan }
                    Text { text: "| 视觉智能筛选系统"; font.pixelSize: 15; font.weight: Font.Bold; color: cTextWhite }
                }
                Item { Layout.fillWidth: true }
                Row { spacing: 16
                    Row { spacing: 6
                        Rectangle { width: 6; height: 6; radius: 3; color: cGreen; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "系统正常"; font.pixelSize: 12; color: cTextSec }
                    }
                    Rectangle { width: 1; height: 18; color: Qt.rgba(0/255,0/255,0/255,0.06) }
                    Text { text: "帧率: 10fps"; font.pixelSize: 12; color: cTextSec }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 14
            Item {
                Layout.preferredWidth: 60; Layout.fillHeight: true
                Rectangle {
                    anchors.fill: parent; radius: cRadius
                    color: Qt.rgba(232/255,248/255,238/255,0.55)
                    border.color: Qt.rgba(100/255,116/255,139/255,0.10); border.width: 1
                    ColumnLayout {
                        anchors.centerIn: parent; spacing: 18; anchors.verticalCenterOffset: -30
                        Item {
                            Layout.preferredWidth: 40; Layout.preferredHeight: 40
                            Rectangle {
                                anchors.fill: parent; radius: 10
                                color: currentPage === 0 ? Qt.rgba(37/255,99/255,235/255,0.12) : "transparent"
                                border.color: currentPage === 0 ? Qt.rgba(0/255,242/255,254/255,0.3) : "transparent"; border.width: 1
                                Rectangle { x: 12; y: 10; width: 4; height: 20; radius: 1; color: cCyan
                                    property real v: 1.0; opacity: currentPage === 0 ? v : 0.25
                                    SequentialAnimation on v { running: currentPage === 0; loops: Animation.Infinite
                                        PauseAnimation { duration: 0 }
                                        NumberAnimation { from: 0.25; to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                                        NumberAnimation { from: 1.0; to: 0.25; duration: 600; easing.type: Easing.InOutSine } } }
                                Rectangle { x: 18; y: 10; width: 4; height: 20; radius: 1; color: cCyan
                                    property real v: 1.0; opacity: currentPage === 0 ? v : 0.25
                                    SequentialAnimation on v { running: currentPage === 0; loops: Animation.Infinite
                                        PauseAnimation { duration: 400 }
                                        NumberAnimation { from: 0.25; to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                                        NumberAnimation { from: 1.0; to: 0.25; duration: 600; easing.type: Easing.InOutSine } } }
                                Rectangle { x: 24; y: 10; width: 4; height: 20; radius: 1; color: cCyan
                                    property real v: 1.0; opacity: currentPage === 0 ? v : 0.25
                                    SequentialAnimation on v { running: currentPage === 0; loops: Animation.Infinite
                                        PauseAnimation { duration: 800 }
                                        NumberAnimation { from: 0.25; to: 1.0; duration: 600; easing.type: Easing.InOutSine }
                                        NumberAnimation { from: 1.0; to: 0.25; duration: 600; easing.type: Easing.InOutSine } } }
                            }
                            MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: currentPage = 0 }
                        }
                        Item {
                            Layout.preferredWidth: 40; Layout.preferredHeight: 40
                            Rectangle {
                                anchors.fill: parent; radius: 10
                                color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.15) : "transparent"
                                border.color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.35) : "transparent"; border.width: 1
                                Repeater {
                                    model: 3
                                    Rectangle {
                                        x: 8; y: 8; width: 24; height: 24; radius: 12
                                        color: "transparent"; border.color: Qt.rgba(8/255,145/255,178/255,0.4); border.width: 1
                                        property real s: 1.0; property real o: 0.5; scale: s; opacity: o
                                        SequentialAnimation on s { running: currentPage === 1; loops: Animation.Infinite
                                            PauseAnimation { duration: index * 500 }
                                            NumberAnimation { from: 1.0; to: 2.2; duration: 1600; easing.type: Easing.OutCubic }
                                            NumberAnimation { from: 2.2; to: 1.0; duration: 0 } }
                                        SequentialAnimation on o { running: currentPage === 1; loops: Animation.Infinite
                                            PauseAnimation { duration: index * 500 }
                                            NumberAnimation { from: 0.5; to: 0.0; duration: 1600; easing.type: Easing.OutCubic }
                                            NumberAnimation { from: 0.0; to: 0.5; duration: 0 } }
                                    }
                                }
                                Rectangle { x: 14; y: 14; width: 12; height: 12; radius: 6; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.7) : cTextSec }
                                Rectangle { x: 7; y: 7; width: 5; height: 5; radius: 2.5; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.55) : cTextDim }
                                Rectangle { x: 28; y: 7; width: 5; height: 5; radius: 2.5; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.55) : cTextDim }
                                Rectangle { x: 16; y: 28; width: 5; height: 5; radius: 2.5; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.55) : cTextDim }
                                Rectangle { x: 10; y: 9; width: 8; height: 1; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.25) : cTextDim; rotation: -45 }
                                Rectangle { x: 24; y: 9; width: 8; height: 1; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.25) : cTextDim; rotation: 45 }
                                Rectangle { x: 16; y: 20; width: 8; height: 1; color: currentPage === 1 ? Qt.rgba(8/255,145/255,178/255,0.25) : cTextDim }
                            }
                            MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: currentPage = 1 }
                        }
                    }
                }
            }
            StackLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: currentPage
                RowLayout { spacing: 14; Layout.fillWidth: true; Layout.fillHeight: true
                    Rectangle {
                        id: camPane; Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 0.65
                        radius: cRadius; color: cCardBg; border.color: cCardBorder; border.width: 1; clip: true
                        DropShadow { anchors.fill: camPane; source: camPane; horizontalOffset: 0; verticalOffset: 0; color: cGlowSoft; radius: 24; samples: 28; transparentBorder: true }
                        ColumnLayout { anchors.fill: parent; spacing: 0
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 34; color: Qt.rgba(232/255,248/255,238/255,0.55)
                                RowLayout { anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                                    Rectangle { width: 6; height: 6; radius: 3; color: cCyan }
                                    Text { text: "相机画面"; font.pixelSize: 12; color: cTextSec }
                                    Item { Layout.fillWidth: true }
                                    Row { spacing: 4
                                        Rectangle { width: 5; height: 5; radius: 2; color: "#FF4444"; anchors.verticalCenter: parent.verticalCenter
                                            SequentialAnimation on opacity { loops: Animation.Infinite
                                                PropertyAnimation { to: 0.2; duration: 800 }
                                                PropertyAnimation { to: 1.0; duration: 800 } } }
                                        Text { text: "LIVE"; font.pixelSize: 9; color: "#FF4444"; font.weight: Font.Bold }
                                    }
                                    Rectangle { width: 1; height: 14; color: Qt.rgba(0/255,0/255,0/255,0.06) }
                                    Text { text: backend.currentFile; font.pixelSize: 11; color: cTextDim }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.fillHeight: true; color: "transparent"
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: parent.width - 24
                                    height: parent.height - 24
                                    radius: 6
                                    color: Qt.rgba(232/255,248/255,238/255,0.55)
                                    border.color: Qt.rgba(100/255, 116/255, 139/255, 0.12)
                                    border.width: 1
                                    Image {
                                        anchors.fill: parent; anchors.margins: 2
                                        fillMode: Image.PreserveAspectFit
                                        source: "image://camera/live?" + backend.frameCounter
                                        cache: false
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; 
                                Layout.preferredHeight: 28; 
                                color: Qt.rgba(232/255,248/255,238/255,0.55)
                                RowLayout { anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                                    Text { text: "分辨率 1280x720"; font.pixelSize: 10; color: cTextDim }
                                    Item { Layout.fillWidth: true }
                                    Text { text: "模式 " + (workMode === 0 ? "直接选择" : "智能匹配"); font.pixelSize: 10; color: cTextDim }
                                    Item { Layout.fillWidth: true }
                                    Rectangle { width: 5; height: 5; radius: 2; color: backend.detectionSource === "AI" ? "#059669" : "#94A3B8"; anchors.verticalCenter: parent.verticalCenter }
                                    Text { text: backend.detectionSource; font.pixelSize: 10; color: cTextDim }
                                }
                            }
                        }
                    }
                    Rectangle {
                        id: ctrlPane; Layout.preferredWidth: 340; Layout.fillHeight: true; radius: cRadius
                        color: cCardBg; border.color: cCardBorder; border.width: 1
                        DropShadow { anchors.fill: ctrlPane; source: ctrlPane; horizontalOffset: 0; verticalOffset: 0; color: cGlowSoft; radius: 24; samples: 28; transparentBorder: true }
                        ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 10
                            RowLayout { Layout.fillWidth: true
                                Text { text: "控制中心"; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                                Item { Layout.fillWidth: true }
                                Rectangle { width: 6; height: 6; radius: 3; color: backend.statusColor }
                            }
                            Rectangle { Layout.fillWidth: true; height: 1
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "transparent" }
                                    GradientStop { position: 0.5; color: Qt.rgba(0/255,0/255,0/255,0.06) }
                                    GradientStop { position: 1.0; color: "transparent" } } }
                            Text { text: "工作模式"; font.pixelSize: 11; color: cTextSec; bottomPadding: -4 }
                            RowLayout {
                                Layout.fillWidth: true; spacing: 6
                                Rectangle {
                                    Layout.fillWidth: true; Layout.preferredHeight: 34; radius: cRadiusSm
                                    color: workMode === 0 ? Qt.rgba(37/255,99/255,235/255,0.12) : Qt.rgba(0/255,0/255,0/255,0.15)
                                    border.color: workMode === 0 ? Qt.rgba(37/255,99/255,235/255,0.25) : "transparent"; border.width: 1
                                    Text { anchors.centerIn: parent; text: "直接选择"; font.pixelSize: 12; color: workMode === 0 ? cCyan : cTextSec }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: workMode = 0 }
                                }
                                Rectangle {
                                    Layout.fillWidth: true; Layout.preferredHeight: 34; radius: cRadiusSm
                                    color: workMode === 1 ? Qt.rgba(37/255,99/255,235/255,0.12) : Qt.rgba(0/255,0/255,0/255,0.15)
                                    border.color: workMode === 1 ? Qt.rgba(37/255,99/255,235/255,0.25) : "transparent"; border.width: 1
                                    Text { anchors.centerIn: parent; text: "智能匹配"; font.pixelSize: 12; color: workMode === 1 ? cCyan : cTextSec }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: workMode = 1 }
                                }
                            }
                            Rectangle {
                                visible: workMode === 0
                                Layout.fillWidth: true; Layout.preferredHeight: 34; radius: cRadiusSm
                                color: Qt.rgba(232/255,248/255,238/255,0.55); border.color: Qt.rgba(37/255,99/255,235/255,0.12); border.width: 1
                                ComboBox {
                                    id: screwCombo; anchors.fill: parent; anchors.margins: 1
                                    model: screwListModel; textRole: "name"
                                    background: Item {}
                                    contentItem: Text { leftPadding: 10; verticalAlignment: Text.AlignVCenter; text: screwCombo.displayText; font.pixelSize: 12; color: cTextWhite }
                                    indicator: Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "\u25bc"; font.pixelSize: 9; color: cTextSec }
                                    popup: Popup {
                                        y: parent.height + 3; width: parent.width; padding: 3; clip: true
                                        background: Rectangle { radius: cRadiusSm; color: "#FFF9E6"; border.color: Qt.rgba(200/255,180/255,120/255,0.35); border.width: 1 }
                                        contentItem: ListView {
                                            clip: true; implicitHeight: contentHeight
                                            model: screwCombo.delegateModel; currentIndex: screwCombo.currentIndex
                                            delegate: ItemDelegate {
                                                width: parent.width; height: 30
                                                background: Rectangle { radius: 5; color: screwCombo.currentIndex === index ? Qt.rgba(200/255,180/255,120/255,0.3) : "transparent" }
                                                contentItem: Text { leftPadding: 10; text: name; color: "#3D2C25"; font.pixelSize: 12 }
                                            }
                                        }
                                        enter: Transition {
                                            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 } }
                                        exit: Transition {
                                            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 150 } }
                                    }
                                    onActivated: backend.selectScrew(screwListModel.get(index).id)
                                }
                            }
                            Rectangle {
                                id: stCard; Layout.fillWidth: true; Layout.preferredHeight: 62; radius: cRadiusSm
                                color: Qt.rgba(210/255, 238/255, 220/255, 0.7); border.color: Qt.rgba(100/255,116/255,139/255,0.10); border.width: 1
                                DropShadow { anchors.fill: stCard; source: stCard; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                                ColumnLayout { anchors.fill: parent; anchors.margins: 12; spacing: 3
                                    Row { spacing: 8
                                        Rectangle { width: 7; height: 7; radius: 3; color: backend.statusColor
                                            SequentialAnimation on opacity { loops: Animation.Infinite; running: backend.statusText === "分析中..."
                                                PropertyAnimation { to: 0.15; duration: 500 }
                                                PropertyAnimation { to: 1.0; duration: 500 } } }
                                        Text { text: backend.statusText; font.pixelSize: 13; font.weight: Font.Bold; color: cTextWhite }
                                    }
                                    Text { text: "当前源 " + backend.currentFile; font.pixelSize: 10; color: cTextSec }
                                }
                            }
                            Rectangle {
                                visible: workMode === 1
                                Layout.fillWidth: true; Layout.preferredHeight: 60; radius: cRadiusSm
                                color: Qt.rgba(210/255, 238/255, 220/255, 0.7); border.color: Qt.rgba(100/255,116/255,139/255,0.10); border.width: 1
                                DropShadow { anchors.fill: parent; source: parent; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                                ColumnLayout { anchors.fill: parent; anchors.margins: 12; spacing: 3
                                    Row { spacing: 6
                                        Text { text: "◆"; font.pixelSize: 10; color: cGold }
                                        Text { text: "匹配结果"; font.pixelSize: 10; color: cTextSec }
                                    }
                                    Row { spacing: 14 }
                                    Row { spacing: 14
                                        Text { text: backend.matchName; font.pixelSize: 13; font.weight: Font.Bold; color: backend.matchName !== "--" ? cTextWhite : cTextSec }
                                        Text { text: "偏差 " + (backend.matchDeviation > 0 ? backend.matchDeviation.toFixed(3) + "mm" : "--"); font.pixelSize: 11; color: backend.matchDeviation > 0 && backend.matchDeviation <= 0.5 ? cGreen : cTextSec }
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 84; radius: cRadiusSm
                                color: Qt.rgba(210/255, 238/255, 220/255, 0.7); border.color: Qt.rgba(100/255,116/255,139/255,0.10); border.width: 1
                                DropShadow { anchors.fill: parent; source: parent; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                                RowLayout { anchors.fill: parent; anchors.margins: 8; spacing: 3
                                    Item { Layout.fillWidth: true; Layout.fillHeight: true
                                        ColumnLayout { anchors.centerIn: parent; spacing: 0
                                            Text { text: "直径"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: backend.measuredDiameter > 0 ? backend.measuredDiameter.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredDiameter > 0 ? cCyan : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter } } }
                                    Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(37/255,99/255,235/255,0.08) }
                                    Item { Layout.fillWidth: true; Layout.fillHeight: true
                                        ColumnLayout { anchors.centerIn: parent; spacing: 0
                                            Text { text: "长度"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: backend.measuredLength > 0 ? backend.measuredLength.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredLength > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter } } }
                                    Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(37/255,99/255,235/255,0.08) }
                                    Item { Layout.fillWidth: true; Layout.fillHeight: true
                                        ColumnLayout { anchors.centerIn: parent; spacing: 0
                                            Text { text: "宽度"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: backend.measuredWidth > 0 ? backend.measuredWidth.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredWidth > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                            Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter } } }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true; spacing: 6
                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 40; radius: cRadiusSm; color: Qt.rgba(210/255, 238/255, 220/255, 0.55); border.color: Qt.rgba(0/255,242/255,254/255,0.05); border.width: 1
                                    ColumnLayout { anchors.centerIn: parent; spacing: 0
                                        Text { text: backend.detectionCount; font.pixelSize: 18; font.weight: Font.Light; color: cCyan; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: "检测次数"; font.pixelSize: 8; color: cTextSec; Layout.alignment: Qt.AlignHCenter } } }
                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 40; radius: cRadiusSm; color: Qt.rgba(210/255, 238/255, 220/255, 0.55); border.color: Qt.rgba(0/255,242/255,254/255,0.05); border.width: 1
                                    ColumnLayout { anchors.centerIn: parent; spacing: 0
                                        Text { text: "±" + backend.tolerance.toFixed(2) + "mm"; font.pixelSize: 18; font.weight: Font.Light; color: cGold; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: "测量精度"; font.pixelSize: 8; color: cTextSec; Layout.alignment: Qt.AlignHCenter } } }
                            }
                            Item { Layout.fillHeight: true }
                            Rectangle {
                                id: btnA; property bool h: false
                                Layout.fillWidth: true; Layout.preferredHeight: 48; radius: cRadiusSm
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "#2563EB" }
                                    GradientStop { position: 1.0; color: "#4F46E5" }
                                }
                                DropShadow {
                                    anchors.fill: btnA; source: btnA
                                    horizontalOffset: 0; verticalOffset: 0
                                    color: Qt.rgba(37/255,99/255,235/255,btnA.h ? 0.5 : 0.25)
                                    radius: btnA.h ? 24 : 14; samples: 28; transparentBorder: true
                                    Behavior on color { ColorAnimation { duration: 200 } }
                                    Behavior on radius { NumberAnimation { duration: 200 } }
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: workMode === 0 ? "确认选择" : "开始分析"
                                    color: "#ffffff"; font.pixelSize: 14; font.weight: Font.Bold
                                }
                                Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(255/255,255/255,255/255,btnA.h ? 0.08 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                                MouseArea {
                                    anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: workMode === 0 ? backend.selectScrew(screwListModel.get(screwCombo.currentIndex).id) : backend.startAnalysis()
                                    onEntered: btnA.h = true; onExited: btnA.h = false; onPressed: parent.opacity = 0.85; onReleased: parent.opacity = 1.0
                                }
                                Behavior on opacity { NumberAnimation { duration: 80 } }
                            }
                            Rectangle {
                                id: btnN; visible: workMode !== 0; property bool h: false
                                Layout.fillWidth: true; Layout.preferredHeight: 44; radius: cRadiusSm; color: Qt.rgba(255/255,255/255,255/255,0.02); border.color: Qt.rgba(0/255,242/255,254/255,btnN.h ? 0.35 : 0.12); border.width: 1; Behavior on border.color { ColorAnimation { duration: 200 } }
                                Text { anchors.centerIn: parent; text: "下一个样本"; font.pixelSize: 13; color: btnN.h ? cTextWhite : cTextSec; Behavior on color { ColorAnimation { duration: 200 } } }
                                Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(0/255,242/255,254/255,btnN.h ? 0.06 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                                MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: backend.nextSample(); onEntered: btnN.h = true; onExited: btnN.h = false; onPressed: parent.opacity = 0.8; onReleased: parent.opacity = 1.0 }
                                Behavior on opacity { NumberAnimation { duration: 80 } }
                            }
                            Rectangle {
                                id: btnC; property bool h: false
                                Layout.fillWidth: true; Layout.preferredHeight: 44; radius: cRadiusSm; color: Qt.rgba(255/255,255/255,255/255,0.02); border.color: Qt.rgba(255/255,215/255,0/255,btnC.h ? 0.35 : 0.10); border.width: 1; Behavior on border.color { ColorAnimation { duration: 200 } }
                                Text { anchors.centerIn: parent; text: "下达指令"; font.pixelSize: 13; color: btnC.h ? "#F5A623" : Qt.rgba(255/255,215/255,0/255,0.6); Behavior on color { ColorAnimation { duration: 200 } } }
                                Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(255/255,215/255,0/255,btnC.h ? 0.06 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                                MouseArea { anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: backend.sendCommand(); onEntered: btnC.h = true; onExited: btnC.h = false; onPressed: parent.opacity = 0.8; onReleased: parent.opacity = 1.0 }
                                Behavior on opacity { NumberAnimation { duration: 80 } }
                            }
                        }
                    }
                }
                RowLayout { spacing: 14; Layout.fillWidth: true; Layout.fillHeight: true
                    Rectangle {
                        id: aiCam; Layout.fillWidth: true; Layout.fillHeight: true
                        radius: cRadius; color: cCardBg; border.color: cCardBorder; border.width: 1; clip: true
                        DropShadow { anchors.fill: aiCam; source: aiCam; horizontalOffset: 0; verticalOffset: 0; color: cGlowSoft; radius: 24; samples: 28; transparentBorder: true }
                        ColumnLayout { anchors.fill: parent; spacing: 0
                            Rectangle {
                                Layout.fillWidth: true; 
                                Layout.preferredHeight: 34; 
                                radius: cRadiusSm // 增加圆角
                                color: Qt.rgba(232/255,248/255,238/255,0.55)
                                RowLayout { anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                                    Rectangle { width: 6; height: 6; radius: 3; color: Qt.rgba(255/255,107/255,157/255,0.8) }
                                    Text { text: "AI 识别画面"; font.pixelSize: 12; color: cTextSec }
                                    Item { Layout.fillWidth: true }
                                    Row { spacing: 4
                                        Rectangle { width: 5; height: 5; radius: 2; color: "#FF4444"; anchors.verticalCenter: parent.verticalCenter
                                            SequentialAnimation on opacity { loops: Animation.Infinite
                                                PropertyAnimation { to: 0.2; duration: 800 }
                                                PropertyAnimation { to: 1.0; duration: 800 } } }
                                        Text { text: "LIVE"; font.pixelSize: 9; color: "#FF4444"; font.weight: Font.Bold }
                                    }
                                    Rectangle { width: 1; height: 14; color: Qt.rgba(0/255,0/255,0/255,0.06) }
                                    Text { text: backend.currentFile; font.pixelSize: 11; color: cTextDim }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.fillHeight: true; color: "transparent"
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: parent.width - 24
                                    height: parent.height - 24
                                    radius: 6
                                    color: Qt.rgba(232/255,248/255,238/255,0.55)
                                    border.color: Qt.rgba(100/255, 116/255, 139/255, 0.12)
                                    border.width: 1
                                    Image {
                                        anchors.fill: parent; anchors.margins: 2
                                        fillMode: Image.PreserveAspectFit
                                        source: "image://camera/live?" + backend.frameCounter
                                        cache: false
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 28; color: Qt.rgba(232/255,248/255,238/255,0.55)
                                RowLayout { anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                                    Text { text: "AI 推理待接入"; font.pixelSize: 10; color: cTextDim }
                                    Item { Layout.fillWidth: true } }
                            }
                        }
                    }
                    Rectangle {
                        id: aiCtrl; Layout.preferredWidth: 340; Layout.fillHeight: true; radius: cRadius
                        color: cCardBg; border.color: cCardBorder; border.width: 1
                        DropShadow { anchors.fill: aiCtrl; source: aiCtrl; horizontalOffset: 0; verticalOffset: 0; color: cGlowPurple; radius: 24; samples: 28; transparentBorder: true }
                        ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 10
                            RowLayout { Layout.fillWidth: true
                                Text { text: "AI 识别中心"; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                                Item { Layout.fillWidth: true }
                                Rectangle { width: 6; height: 6; radius: 3; color: Qt.rgba(255/255,107/255,157/255,0.8) }
                            }
                            Rectangle { Layout.fillWidth: true; height: 1
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "transparent" }
                                    GradientStop { position: 0.5; color: Qt.rgba(0/255,0/255,0/255,0.06) }
                                    GradientStop { position: 1.0; color: "transparent" } } }
                            Rectangle {
                                Layout.fillWidth: true; Layout.fillHeight: true; radius: cRadiusSm
                                color: Qt.rgba(210/255,238/255,220/255,0.7); border.color: Qt.rgba(37/255,99/255,235/255,0.10); border.width: 1
                                ColumnLayout { anchors.fill: parent; anchors.margins: 14; spacing: 8
                                    RowLayout { spacing: 8
                                        Rectangle { width: 8; height: 8; radius: 4; color: backend.aiLoaded ? "#059669" : "#94A3B8" }
                                        Text { text: "AI 模型状态"; font.pixelSize: 11; color: cTextSec }
                                        Item { Layout.fillWidth: true }
                                        Text { text: backend.aiLoaded ? "已加载" : "未加载"; font.pixelSize: 12; font.weight: Font.Bold; color: backend.aiLoaded ? "#059669" : cTextSec }
                                    }
                                    Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(0/255,0/255,0/255,0.05) }
                                    RowLayout { spacing: 8
                                        Column { spacing: 4; Layout.fillWidth: true
                                            Text { text: "推理后端"; font.pixelSize: 10; color: cTextSec }
                                            Text { text: backend.aiBackend; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                                        }
                                        Column { spacing: 4; Layout.fillWidth: true
                                            Text { text: "检测源"; font.pixelSize: 10; color: cTextSec }
                                            Text { text: backend.detectionSource; font.pixelSize: 14; font.weight: Font.Bold; color: backend.detectionSource === "AI" ? "#059669" : cTextWhite }
                                        }
                                    }
                                    Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(0/255,0/255,0/255,0.05) }
                                    RowLayout { spacing: 8
                                        Column { spacing: 4; Layout.fillWidth: true
                                            Text { text: "本帧检测数"; font.pixelSize: 10; color: cTextSec }
                                            Text { text: backend.aiScrewCount; font.pixelSize: 22; font.weight: Font.Light; color: backend.aiScrewCount > 0 ? "#2563EB" : cTextSec }
                                        }
                                        Column { spacing: 4; Layout.fillWidth: true
                                            Text { text: "最大置信度"; font.pixelSize: 10; color: cTextSec }
                                            Item { Layout.preferredHeight: 22
                                                Text { text: backend.aiConfidence > 0 ? backend.aiConfidence.toFixed(3) : "--"; font.pixelSize: 16; font.weight: Font.Light; color: backend.aiConfidence > 0.5 ? "#059669" : backend.aiConfidence > 0.25 ? "#D97706" : cTextSec; anchors.left: parent.left }
                                            }
                                        }
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 50; radius: cRadiusSm; color: Qt.rgba(210/255,238/255,220/255,0.55); border.color: Qt.rgba(37/255,99/255,235/255,0.05); border.width: 1
                                RowLayout { anchors.fill: parent; anchors.margins: 8; spacing: 6
                                    Column { spacing: 2; Layout.fillWidth: true
                                        Text { text: "AI 状态"; font.pixelSize: 9; color: cTextSec }
                                        Text { text: backend.aiLoaded ? "运行中" : "未激活"; font.pixelSize: 12; font.weight: Font.Bold; color: backend.aiLoaded ? "#059669" : cTextSec }
                                    }
                                    Rectangle { Layout.fillHeight: true; width: 1; color: Qt.rgba(0/255,0/255,0/255,0.05) }
                                    Column { spacing: 2; Layout.fillWidth: true
                                        Text { text: "检测源"; font.pixelSize: 9; color: cTextSec }
                                        Text { text: backend.detectionSource; font.pixelSize: 12; font.weight: Font.Bold; color: backend.detectionSource === "AI" ? "#2563EB" : cTextSec }
                                    }
                                    Rectangle { Layout.fillHeight: true; width: 1; color: Qt.rgba(0/255,0/255,0/255,0.05) }
                                    Column { spacing: 2; Layout.fillWidth: true
                                        Text { text: "置信度"; font.pixelSize: 9; color: cTextSec }
                                        Text { text: backend.aiConfidence > 0 ? backend.aiConfidence.toFixed(3) : "--"; font.pixelSize: 12; font.weight: Font.Bold; color: backend.aiConfidence > 0.5 ? "#059669" : "#D97706" }
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