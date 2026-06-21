import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: root; visible: true
    width: 1280; height: 800
    minimumWidth: 1024; minimumHeight: 680
    title: "视觉智能筛选系统 v2.0"

    readonly property color cBgStart:     "#070B14"
    readonly property color cBgEnd:       "#0F1A2E"
    readonly property color cCardBg:      Qt.rgba(20/255, 28/255, 47/255, 0.65)
    readonly property color cCardBorder:  Qt.rgba(0/255, 242/255, 254/255, 0.20)
    readonly property color cCyan:        "#00F2FE"
    readonly property color cGreen:       "#00FFCC"
    readonly property color cGold:        "#FFD700"
    readonly property color cTextWhite:   "#FFFFFF"
    readonly property color cTextSec:     Qt.rgba(255/255, 255/255, 255/255, 0.55)
    readonly property color cTextDim:     Qt.rgba(255/255, 255/255, 255/255, 0.3)
    readonly property color cGlowSoft:    Qt.rgba(0/255, 242/255, 254/255, 0.12)
    readonly property color cGlowPurple:  Qt.rgba(118/255, 75/255, 162/255, 0.3)
    readonly property int   cRadius:      12
    readonly property int   cRadiusSm:    8
    // Background
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: cBgStart }
            GradientStop { position: 1.0; color: cBgEnd }
        }
        Canvas {
            anchors.fill: parent; opacity: 0.035
            onPaint: {
                var ctx = getContext("2d");
                ctx.strokeStyle = Qt.rgba(0/255,242/255,254/255,1);
                ctx.lineWidth = 0.5; var step = 64;
                for (var x = step; x < width; x += step) {
                    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
                }
                for (var y = step; y < height; y += step) {
                    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
                }
            }
        }
    }

    RowLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 14

        // Sidebar
        Item {
            Layout.preferredWidth: 60; Layout.fillHeight: true
            Rectangle {
                anchors.fill: parent; radius: cRadius
                color: Qt.rgba(15/255,21/255,36/255,0.7)
                border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                ColumnLayout {
                    anchors.centerIn: parent; spacing: 18
                    Item {
                        Layout.preferredWidth: 40; Layout.preferredHeight: 40
                        Rectangle {
                            anchors.fill: parent; radius: 10
                            color: Qt.rgba(0/255,242/255,254/255,0.12)
                            border.color: Qt.rgba(0/255,242/255,254/255,0.3); border.width: 1
                            Rectangle { x: 0; y: 10; width: 3; height: 20; radius: 1; color: cCyan }
                            Rectangle { x: 10; y: 14; width: 4; height: 12; radius: 1; color: cCyan }
                            Rectangle { x: 18; y: 10; width: 4; height: 16; radius: 1; color: cCyan }
                            Rectangle { x: 26; y: 16; width: 4; height: 8; radius: 1; color: cCyan }
                        }
                    }
                    Item {
                        Layout.preferredWidth: 40; Layout.preferredHeight: 40
                        Rectangle {
                            anchors.fill: parent; radius: 10; color: "transparent"
                            Rectangle { x: 10; y: 8; width: 20; height: 3; radius: 1; color: cTextSec }
                            Rectangle { x: 10; y: 14; width: 20; height: 3; radius: 1; color: cTextSec }
                            Rectangle { x: 10; y: 20; width: 20; height: 3; radius: 1; color: cTextSec }
                            Rectangle { x: 10; y: 26; width: 14; height: 3; radius: 1; color: cTextSec }
                        }
                    }
                    Item {
                        Layout.preferredWidth: 40; Layout.preferredHeight: 40
                        Rectangle {
                            anchors.fill: parent; radius: 10; color: "transparent"
                            Rectangle { x: 14; y: 8; width: 12; height: 12; radius: 6; color: "transparent"; border.color: cTextSec; border.width: 1 }
                            Rectangle { x: 16; y: 10; width: 8; height: 8; radius: 4; color: cTextSec }
                        }
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 14

            // Top Bar
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 48; radius: cRadiusSm
                color: Qt.rgba(20/255,28/255,47/255,0.4)
                border.color: Qt.rgba(0/255,242/255,254/255,0.10); border.width: 1
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                    Row { spacing: 10
                        Rectangle { width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter; color: cCyan
                            SequentialAnimation on opacity { loops: Animation.Infinite
                                PropertyAnimation { to: 0.3; duration: 1200 }
                                PropertyAnimation { to: 1.0; duration: 1200 }
                            }
                        }
                        Text { text: "视觉智能筛选系统"; font.pixelSize: 15; font.weight: Font.Bold; color: cTextWhite; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "v2.0"; font.pixelSize: 10; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                    }
                    Item { Layout.fillWidth: true }
                    Row { spacing: 16
                        Row { spacing: 6
                            Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: cGreen }
                            Text { text: "系统正常"; font.pixelSize: 12; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                        }
                        Rectangle { width: 1; height: 18; color: Qt.rgba(255/255,255/255,255/255,0.06); anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "帧率: 10fps"; font.pixelSize: 12; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
            }

            RowLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 14

                // Camera Pane
                Rectangle {
                    id: cameraPane
                    Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 0.65
                    radius: cRadius; color: cCardBg; border.color: cCardBorder; border.width: 1; clip: true
                    Rectangle {
                        anchors.fill: parent; anchors.margins: -6; radius: cRadius + 6
                        color: "transparent"; border.color: Qt.rgba(0/255,242/255,254/255,0.04); border.width: 1; z: -1
                    }
                    DropShadow {
                        anchors.fill: cameraPane; source: cameraPane
                        horizontalOffset: 0; verticalOffset: 0
                        color: cGlowSoft; radius: 24; samples: 28; transparentBorder: true
                    }
                    ColumnLayout { anchors.fill: parent; spacing: 0
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 34
                            color: Qt.rgba(0/255,0/255,0/255,0.25)
                            RowLayout { anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                                Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: cCyan }
                                Text { text: "相机画面"; font.pixelSize: 12; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                                Item { Layout.fillWidth: true }
                                Row { spacing: 4; anchors.verticalCenter: parent.verticalCenter
                                    Rectangle { width: 5; height: 5; radius: 2; anchors.verticalCenter: parent.verticalCenter; color: "#FF4444"
                                        SequentialAnimation on opacity { loops: Animation.Infinite
                                            PropertyAnimation { to: 0.2; duration: 800 }
                                            PropertyAnimation { to: 1.0; duration: 800 }
                                        }
                                    }
                                    Text { text: "LIVE"; font.pixelSize: 9; color: "#FF4444"; font.weight: Font.Bold }
                                }
                                Rectangle { width: 1; height: 14; color: Qt.rgba(255/255,255/255,255/255,0.06); anchors.verticalCenter: parent.verticalCenter }
                                Text { text: backend.currentFile; font.pixelSize: 11; color: cTextDim; anchors.verticalCenter: parent.verticalCenter }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true; Layout.fillHeight: true; color: "#080C18"
                            Image {
                                id: cameraFeed; anchors.fill: parent; anchors.margins: 1
                                fillMode: Image.PreserveAspectFit
                                source: "image://camera/live?" + backend.frameCounter; cache: false
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 28
                            color: Qt.rgba(0/255,0/255,0/255,0.3)
                            RowLayout { anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                                Text { text: "分辨率: 1280x720"; font.pixelSize: 10; color: cTextDim }
                                Item { Layout.fillWidth: true }
                                Text { text: "检测模式: " + modeCombo.currentIndex + 1; font.pixelSize: 10; color: cTextDim }
                            }
                        }
                    }
                }

                // Control Panel
                Rectangle {
                    id: controlPane
                    Layout.preferredWidth: 340; Layout.fillHeight: true; radius: cRadius
                    color: cCardBg; border.color: cCardBorder; border.width: 1
                    Rectangle {
                        anchors.fill: parent; anchors.margins: -6; radius: cRadius + 6
                        color: "transparent"; border.color: Qt.rgba(0/255,242/255,254/255,0.04); border.width: 1; z: -1
                    }
                    DropShadow {
                        anchors.fill: controlPane; source: controlPane
                        horizontalOffset: 0; verticalOffset: 0
                        color: cGlowSoft; radius: 24; samples: 28; transparentBorder: true
                    }
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 16; spacing: 10
                        RowLayout { Layout.fillWidth: true
                            Text { text: "控制中心"; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                            Item { Layout.fillWidth: true }
                            Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: backend.statusColor }
                        }
                        Rectangle { Layout.fillWidth: true; height: 1
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "transparent" }
                                GradientStop { position: 0.5; color: Qt.rgba(0/255,242/255,254/255,0.12) }
                                GradientStop { position: 1.0; color: "transparent" }
                            }
                        }
                        Text { text: "作业模式"; font.pixelSize: 11; color: cTextSec; bottomPadding: -4 }
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 34; radius: cRadiusSm
                            color: Qt.rgba(0/255,0/255,0/255,0.25)
                            border.color: Qt.rgba(0/255,242/255,254/255,0.12); border.width: 1
                            ComboBox {
                                id: modeCombo; anchors.fill: parent; anchors.margins: 1
                                model: ["螺丝", "螺母垫片", "其他"]; currentIndex: 0
                                background: Item {}
                                contentItem: Text { leftPadding: 10; verticalAlignment: Text.AlignVCenter; text: modeCombo.displayText; font.pixelSize: 12; color: cTextWhite }
                                indicator: Text { anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter; text: "▼"; font.pixelSize: 9; color: cTextSec }
                                popup: Popup {
                                    y: parent.height + 3; width: parent.width; padding: 3
                                    background: Rectangle { radius: cRadiusSm; color: "#0F1A2E"; border.color: Qt.rgba(0/255,242/255,254/255,0.15); border.width: 1 }
                                    contentItem: ListView {
                                        clip: true; implicitHeight: contentHeight
                                        model: modeCombo.delegateModel; currentIndex: modeCombo.currentIndex
                                        delegate: ItemDelegate {
                                            width: parent.width; height: 30
                                            background: Rectangle { radius: 5; color: modeCombo.currentIndex === index ? Qt.rgba(0/255,242/255,254/255,0.12) : "transparent" }
                                            contentItem: Text { leftPadding: 10; verticalAlignment: Text.AlignVCenter; text: modelData; color: cTextWhite; font.pixelSize: 12 }
                                        }
                                    }
                                }
                            }
                        }
                        Rectangle {
                            id: statusCard
                            Layout.fillWidth: true; Layout.preferredHeight: 62; radius: cRadiusSm
                            color: Qt.rgba(0/255,0/255,0/255,0.2)
                            border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                            DropShadow { anchors.fill: statusCard; source: statusCard; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                            ColumnLayout { anchors.fill: parent; anchors.margins: 12; spacing: 3
                                Row { spacing: 8
                                    Rectangle { id: statusDot; width: 7; height: 7; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: backend.statusColor
                                        SequentialAnimation on opacity { loops: Animation.Infinite; running: backend.statusText === "分析中..."
                                            PropertyAnimation { to: 0.15; duration: 500 }
                                            PropertyAnimation { to: 1.0; duration: 500 }
                                        }
                                    }
                                    Text { anchors.verticalCenter: parent.verticalCenter; text: backend.statusText; font.pixelSize: 13; font.weight: Font.Bold; color: cTextWhite }
                                }
                                Text { text: "当前源: " + backend.currentFile; font.pixelSize: 10; color: cTextSec }
                            }
                        }
                        Rectangle {
                            id: aiCard
                            Layout.fillWidth: true; Layout.preferredHeight: 60; radius: cRadiusSm
                            color: Qt.rgba(0/255,0/255,0/255,0.2)
                            border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                            DropShadow { anchors.fill: aiCard; source: aiCard; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                            ColumnLayout { anchors.fill: parent; anchors.margins: 12; spacing: 3
                                Row { spacing: 6
                                    Text { text: "●"; font.pixelSize: 10; color: cCyan; anchors.verticalCenter: parent.verticalCenter }
                                    Text { text: "AI 检测结果"; font.pixelSize: 10; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                                }
                                Row { spacing: 14
                                    Text { text: "标签: " + backend.aiResultLabel; font.pixelSize: 11; color: backend.aiResultLabel !== "--" ? cTextWhite : cTextSec }
                                    Text { text: "置信度: " + (backend.aiConfidence > 0 ? (backend.aiConfidence * 100).toFixed(1) + "%" : "--"); font.pixelSize: 11; color: backend.aiConfidence > 0 ? cGreen : cTextSec }
                                }
                            }
                        }
                        Rectangle {
                            id: measCard
                            Layout.fillWidth: true; Layout.preferredHeight: 84; radius: cRadiusSm
                            color: Qt.rgba(0/255,0/255,0/255,0.2)
                            border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                            DropShadow { anchors.fill: measCard; source: measCard; horizontalOffset: 0; verticalOffset: 0; color: Qt.rgba(0/255,242/255,254/255,0.05); radius: 8; samples: 14; transparentBorder: true }
                            RowLayout { anchors.fill: parent; anchors.margins: 8; spacing: 3
                                Item { Layout.fillWidth: true; Layout.fillHeight: true
                                    ColumnLayout { anchors.centerIn: parent; spacing: 0
                                        Text { text: "直径"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: backend.measuredDiameter > 0 ? backend.measuredDiameter.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredDiameter > 0 ? cCyan : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                } }
                                Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(0/255,242/255,254/255,0.06) }
                                Item { Layout.fillWidth: true; Layout.fillHeight: true
                                    ColumnLayout { anchors.centerIn: parent; spacing: 0
                                        Text { text: "长度"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: backend.measuredLength > 0 ? backend.measuredLength.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredLength > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                } }
                                Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(0/255,242/255,254/255,0.06) }
                                Item { Layout.fillWidth: true; Layout.fillHeight: true
                                    ColumnLayout { anchors.centerIn: parent; spacing: 0
                                        Text { text: "宽度"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: backend.measuredWidth > 0 ? backend.measuredWidth.toFixed(2) : "--"; font.pixelSize: 28; font.weight: Font.Light; color: backend.measuredWidth > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                        Text { text: "mm"; font.pixelSize: 9; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                } }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true; spacing: 6
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 40; radius: cRadiusSm; color: Qt.rgba(0/255,0/255,0/255,0.15); border.color: Qt.rgba(0/255,242/255,254/255,0.05); border.width: 1
                                ColumnLayout { anchors.centerIn: parent; spacing: 0
                                    Text { text: "128"; font.pixelSize: 18; font.weight: Font.Light; color: cCyan; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "检测次数"; font.pixelSize: 8; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                }
                            }
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 40; radius: cRadiusSm; color: Qt.rgba(0/255,0/255,0/255,0.15); border.color: Qt.rgba(0/255,242/255,254/255,0.05); border.width: 1
                                ColumnLayout { anchors.centerIn: parent; spacing: 0
                                    Text { text: "96.5%"; font.pixelSize: 18; font.weight: Font.Light; color: cGreen; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "合格率"; font.pixelSize: 8; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                }
                            }
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 40; radius: cRadiusSm; color: Qt.rgba(0/255,0/255,0/255,0.15); border.color: Qt.rgba(0/255,242/255,254/255,0.05); border.width: 1
                                ColumnLayout { anchors.centerIn: parent; spacing: 0
                                    Text { text: "99%"; font.pixelSize: 18; font.weight: Font.Light; color: cGold; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "精度"; font.pixelSize: 8; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        Rectangle {
                            id: btnAnalyze; property bool hovered: false
                            Layout.fillWidth: true; Layout.preferredHeight: 48; radius: cRadiusSm
                            gradient: Gradient {
                                GradientStop { position: 0.0; color: "#667eea" }
                                GradientStop { position: 1.0; color: "#764ba2" }
                            }
                            DropShadow {
                                anchors.fill: btnAnalyze; source: btnAnalyze
                                horizontalOffset: 0; verticalOffset: 0
                                color: Qt.rgba(118/255,75/255,162/255,btnAnalyze.hovered ? 0.5 : 0.25)
                                radius: btnAnalyze.hovered ? 24 : 14; samples: 28; transparentBorder: true
                                Behavior on color { ColorAnimation { duration: 200 } }
                                Behavior on radius { NumberAnimation { duration: 200 } }
                            }
                            Text { anchors.centerIn: parent; text: "开始分析"; color: "#ffffff"; font.pixelSize: 14; font.weight: Font.Bold }
                            Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(255/255,255/255,255/255,btnAnalyze.hovered ? 0.08 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                            MouseArea {
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: backend.startAnalysis()
                                onEntered: btnAnalyze.hovered = true; onExited: btnAnalyze.hovered = false
                                onPressed: parent.opacity = 0.85; onReleased: parent.opacity = 1.0
                            }
                            Behavior on opacity { NumberAnimation { duration: 80 } }
                        }
                        Rectangle {
                            id: btnNext; property bool hovered: false
                            Layout.fillWidth: true; Layout.preferredHeight: 44; radius: cRadiusSm
                            color: Qt.rgba(255/255,255/255,255/255,0.02)
                            border.color: Qt.rgba(0/255,242/255,254/255,btnNext.hovered ? 0.35 : 0.12); border.width: 1
                            Behavior on border.color { ColorAnimation { duration: 200 } }
                            Text { anchors.centerIn: parent; text: "下一个样本"; font.pixelSize: 13; color: btnNext.hovered ? cTextWhite : cTextSec; Behavior on color { ColorAnimation { duration: 200 } } }
                            Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(0/255,242/255,254/255,btnNext.hovered ? 0.06 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                            MouseArea {
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: backend.nextSample()
                                onEntered: btnNext.hovered = true; onExited: btnNext.hovered = false
                                onPressed: parent.opacity = 0.8; onReleased: parent.opacity = 1.0
                            }
                            Behavior on opacity { NumberAnimation { duration: 80 } }
                        }
                        Rectangle {
                            id: btnCommand; property bool hovered: false
                            Layout.fillWidth: true; Layout.preferredHeight: 44; radius: cRadiusSm
                            color: Qt.rgba(255/255,255/255,255/255,0.02)
                            border.color: Qt.rgba(255/255,215/255,0/255,btnCommand.hovered ? 0.35 : 0.10); border.width: 1
                            Behavior on border.color { ColorAnimation { duration: 200 } }
                            Text { anchors.centerIn: parent; text: "下达指令"; font.pixelSize: 13; color: btnCommand.hovered ? "#FFD700" : Qt.rgba(255/255,215/255,0/255,0.6); Behavior on color { ColorAnimation { duration: 200 } } }
                            Rectangle { anchors.fill: parent; radius: parent.radius; color: Qt.rgba(255/255,215/255,0/255,btnCommand.hovered ? 0.06 : 0); Behavior on color { ColorAnimation { duration: 200 } } }
                            MouseArea {
                                anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: backend.sendCommand()
                                onEntered: btnCommand.hovered = true; onExited: btnCommand.hovered = false
                                onPressed: parent.opacity = 0.8; onReleased: parent.opacity = 1.0
                            }
                            Behavior on opacity { NumberAnimation { duration: 80 } }
                        }
                    }
                }
            }
        }
    }
}
