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
    readonly property color cGlowSoft:    Qt.rgba(0/255, 242/255, 254/255, 0.12)

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

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 16

        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 52; radius: 10
            color: Qt.rgba(20/255,28/255,47/255,0.4)
            border.color: Qt.rgba(0/255,242/255,254/255,0.10); border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20
                Row { spacing: 10
                    Rectangle { width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter; color: cCyan
                        SequentialAnimation on opacity { loops: Animation.Infinite
                            PropertyAnimation { to: 0.3; duration: 1200 }
                            PropertyAnimation { to: 1.0; duration: 1200 }
                        }
                    }
                    Text { text: "视觉智能筛选系统"; font.pixelSize: 16; font.weight: Font.Bold; color: cTextWhite }
                    Text { text: "v2.0"; font.pixelSize: 11; color: cTextSec; anchors.verticalCenter: parent.verticalCenter }
                }
                Item { Layout.fillWidth: true }
                Row { spacing: 16
                    Row { spacing: 6
                        Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: cGreen }
                        Text { text: "系统正常"; font.pixelSize: 12; color: cTextSec }
                    }
                    Rectangle { width: 1; height: 20; color: Qt.rgba(255/255,255/255,255/255,0.06); anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "帧率: 10fps"; font.pixelSize: 12; color: cTextSec }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 16

            Rectangle {
                id: cameraPane
                Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 0.65
                radius: 12; color: cCardBg; border.color: cCardBorder; border.width: 1; clip: true
                DropShadow {
                    anchors.fill: parent; source: parent
                    horizontalOffset: 0; verticalOffset: 0
                    color: cGlowSoft; radius: 20; samples: 24; transparentBorder: true
                }
                ColumnLayout { anchors.fill: parent; spacing: 0
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 34
                        color: Qt.rgba(0/255,0/255,0/255,0.25)
                        RowLayout { anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                            Rectangle { width: 6; height: 6; radius: 3; anchors.verticalCenter: parent.verticalCenter; color: cCyan }
                            Text { text: "相机画面"; font.pixelSize: 12; color: cTextSec }
                            Item { Layout.fillWidth: true }
                            Text { text: backend.currentFile; font.pixelSize: 11; color: Qt.rgba(255/255,255/255,255/255,0.3) }
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
                }
            }

            Rectangle {
                id: controlPane
                Layout.preferredWidth: 340; Layout.fillHeight: true; radius: 12
                color: cCardBg; border.color: cCardBorder; border.width: 1
                DropShadow {
                    anchors.fill: parent; source: parent
                    horizontalOffset: 0; verticalOffset: 0
                    color: cGlowSoft; radius: 20; samples: 24; transparentBorder: true
                }
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 20; spacing: 12

                    Text { text: "控制中心"; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                    Rectangle {
                        Layout.fillWidth: true; height: 1
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "transparent" }
                            GradientStop { position: 0.5; color: Qt.rgba(0/255,242/255,254/255,0.15) }
                            GradientStop { position: 1.0; color: "transparent" }
                        }
                    }

                    Text { text: "作业模式选择"; font.pixelSize: 11; color: cTextSec }

                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 38; radius: 8
                        color: Qt.rgba(0/255,0/255,0/255,0.25)
                        border.color: Qt.rgba(0/255,242/255,254/255,0.12); border.width: 1
                        ComboBox {
                            id: modeCombo; anchors.fill: parent; anchors.margins: 1
                            model: ["螺丝", "螺母垫片", "其他"]; currentIndex: 0
                            background: Item {}
                            contentItem: Text { leftPadding: 12; verticalAlignment: Text.AlignVCenter; text: modeCombo.displayText; font.pixelSize: 13; color: cTextWhite }
                            indicator: Text { anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; text: "▼"; font.pixelSize: 10; color: cTextSec }
                            popup: Popup {
                                y: parent.height + 4; width: parent.width; padding: 4
                                background: Rectangle { radius: 8; color: "#0F1A2E"; border.color: Qt.rgba(0/255,242/255,254/255,0.15); border.width: 1 }
                                contentItem: ListView {
                                    clip: true; implicitHeight: contentHeight
                                    model: modeCombo.delegateModel; currentIndex: modeCombo.currentIndex
                                    delegate: ItemDelegate {
                                        width: parent.width; height: 34
                                        background: Rectangle { radius: 6; color: modeCombo.currentIndex === index ? Qt.rgba(0/255,242/255,254/255,0.12) : "transparent" }
                                        contentItem: Text { leftPadding: 12; verticalAlignment: Text.AlignVCenter; text: modelData; color: cTextWhite; font.pixelSize: 12 }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        id: statusCard
                        Layout.fillWidth: true; Layout.preferredHeight: 70; radius: 10
                        color: Qt.rgba(0/255,0/255,0/255,0.2)
                        border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                        DropShadow {
                            anchors.fill: statusCard; source: statusCard
                            horizontalOffset: 0; verticalOffset: 0
                            color: Qt.rgba(0/255,242/255,254/255,0.06)
                            radius: 8; samples: 16; transparentBorder: true
                        }
                        ColumnLayout { anchors.fill: parent; anchors.margins: 14; spacing: 4
                            Row { spacing: 8
                                Rectangle { id: statusDot; width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter; color: backend.statusColor
                                    SequentialAnimation on opacity { loops: Animation.Infinite; running: backend.statusText === "分析中..."
                                        PropertyAnimation { to: 0.2; duration: 600 }
                                        PropertyAnimation { to: 1.0; duration: 600 }
                                    }
                                }
                                Text { anchors.verticalCenter: parent.verticalCenter; text: backend.statusText; font.pixelSize: 14; font.weight: Font.Bold; color: cTextWhite }
                            }
                            Text { text: "当前源: " + backend.currentFile; font.pixelSize: 11; color: cTextSec }
                        }
                    }

                    Rectangle {
                        id: aiCard
                        Layout.fillWidth: true; Layout.preferredHeight: 68; radius: 10
                        color: Qt.rgba(0/255,0/255,0/255,0.2)
                        border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                        DropShadow {
                            anchors.fill: aiCard; source: aiCard
                            horizontalOffset: 0; verticalOffset: 0
                            color: Qt.rgba(0/255,242/255,254/255,0.06)
                            radius: 8; samples: 16; transparentBorder: true
                        }
                        ColumnLayout { anchors.fill: parent; anchors.margins: 14; spacing: 4
                            Row { spacing: 6
                                Text { text: "●"; font.pixelSize: 12; color: cCyan }
                                Text { text: "AI 检测结果 (预留)"; font.pixelSize: 11; color: cTextSec }
                            }
                            Row { spacing: 16
                                Text { text: "标签: " + backend.aiResultLabel; font.pixelSize: 12; color: backend.aiResultLabel !== "--" ? cTextWhite : cTextSec }
                                Text { text: "置信: " + (backend.aiConfidence > 0 ? (backend.aiConfidence * 100).toFixed(1) + "%" : "--"); font.pixelSize: 12; color: backend.aiConfidence > 0 ? cGreen : cTextSec }
                                Rectangle { width: 1; height: 14; anchors.verticalCenter: parent.verticalCenter; color: Qt.rgba(255/255,255/255,255/255,0.06) }
                                Text { text: "模型: --"; font.pixelSize: 12; color: cTextSec }
                            }
                        }
                    }

                    Rectangle {
                        id: measCard
                        Layout.fillWidth: true; Layout.preferredHeight: 92; radius: 10
                        color: Qt.rgba(0/255,0/255,0/255,0.2)
                        border.color: Qt.rgba(0/255,242/255,254/255,0.08); border.width: 1
                        DropShadow {
                            anchors.fill: measCard; source: measCard
                            horizontalOffset: 0; verticalOffset: 0
                            color: Qt.rgba(0/255,242/255,254/255,0.06)
                            radius: 8; samples: 16; transparentBorder: true
                        }
                        RowLayout { anchors.fill: parent; anchors.margins: 10; spacing: 4
                            Item { Layout.fillWidth: true; Layout.fillHeight: true
                                ColumnLayout { anchors.centerIn: parent; spacing: 1
                                    Text { text: "直径"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: backend.measuredDiameter > 0 ? backend.measuredDiameter.toFixed(2) : "--"; font.pixelSize: 30; font.weight: Font.Light; color: backend.measuredDiameter > 0 ? cCyan : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "mm"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                            } }
                            Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(0/255,242/255,254/255,0.08) }
                            Item { Layout.fillWidth: true; Layout.fillHeight: true
                                ColumnLayout { anchors.centerIn: parent; spacing: 1
                                    Text { text: "长度"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: backend.measuredLength > 0 ? backend.measuredLength.toFixed(2) : "--"; font.pixelSize: 30; font.weight: Font.Light; color: backend.measuredLength > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "mm"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                            } }
                            Rectangle { Layout.fillHeight: true; Layout.preferredWidth: 1; color: Qt.rgba(0/255,242/255,254/255,0.08) }
                            Item { Layout.fillWidth: true; Layout.fillHeight: true
                                ColumnLayout { anchors.centerIn: parent; spacing: 1
                                    Text { text: "宽度"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: backend.measuredWidth > 0 ? backend.measuredWidth.toFixed(2) : "--"; font.pixelSize: 30; font.weight: Font.Light; color: backend.measuredWidth > 0 ? cGreen : cTextSec; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: "mm"; font.pixelSize: 10; color: cTextSec; Layout.alignment: Qt.AlignHCenter }
                            } }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    Rectangle {
                        id: btnAnalyze; property bool hovered: false
                        Layout.fillWidth: true; Layout.preferredHeight: 52; radius: 10
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#00C8FF" }
                            GradientStop { position: 1.0; color: "#0099FF" }
                        }
                        DropShadow {
                            anchors.fill: btnAnalyze; source: btnAnalyze
                            horizontalOffset: 0; verticalOffset: 0
                            color: Qt.rgba(0/255,200/255,255/255,btnAnalyze.hovered ? 0.5 : 0.2)
                            radius: btnAnalyze.hovered ? 24 : 16; samples: 28; transparentBorder: true
                            Behavior on color { ColorAnimation { duration: 200 } }
                            Behavior on radius { NumberAnimation { duration: 200 } }
                        }
                        Text { anchors.centerIn: parent; text: "开始分析"; color: "#ffffff"; font.pixelSize: 15; font.weight: Font.Bold }
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
                        Layout.fillWidth: true; Layout.preferredHeight: 48; radius: 8
                        color: Qt.rgba(255/255,255/255,255/255,0.02)
                        border.color: Qt.rgba(0/255,242/255,254/255,btnNext.hovered ? 0.35 : 0.12); border.width: 1
                        Behavior on border.color { ColorAnimation { duration: 200 } }
                        Text { anchors.centerIn: parent; text: "下一个样本"; font.pixelSize: 14; color: btnNext.hovered ? cTextWhite : cTextSec; Behavior on color { ColorAnimation { duration: 200 } } }
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
                        Layout.fillWidth: true; Layout.preferredHeight: 48; radius: 8
                        color: Qt.rgba(255/255,255/255,255/255,0.02)
                        border.color: Qt.rgba(255/255,215/255,0/255,btnCommand.hovered ? 0.35 : 0.10); border.width: 1
                        Behavior on border.color { ColorAnimation { duration: 200 } }
                        Text { anchors.centerIn: parent; text: "下达指令"; font.pixelSize: 14; color: btnCommand.hovered ? "#FFD700" : Qt.rgba(255/255,215/255,0/255,0.6); Behavior on color { ColorAnimation { duration: 200 } } }
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
