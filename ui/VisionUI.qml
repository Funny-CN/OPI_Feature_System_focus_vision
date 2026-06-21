import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

/*
 * VisionUI.qml — 视觉智能筛选系统主界面
 *
 * 风格：深色玻璃质感 + 渐变霓虹强调 (参考 Vision UI Dashboard)
 * 布局：左侧 65% 相机画面 + 右侧 35% 控制面板
 *
 * 后端绑定：backend (VisionBackend 实例，由 main_gui.py 设置)
 */

ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 800
    minimumWidth: 1024
    minimumHeight: 680
    color: "#0f111a"
    title: "视觉智能筛选系统 v2.0"

    // ── 颜色常量 ──────────────────────────────────
    readonly property color cBg:          "#0f111a"
    readonly property color cCard:        Qt.rgba(26/255, 29/255, 45/255, 0.6)
    readonly property color cBorder:      Qt.rgba(255/255,255/255,255/255, 0.08)
    readonly property color cAccent1:     "#667eea"
    readonly property color cAccent2:     "#764ba2"
    readonly property color cText:        "#dfe6e9"
    readonly property color cTextSec:     "#636e72"
    readonly property color cSuccess:     "#00B894"
    readonly property color cDanger:      "#FF7675"
    readonly property color cGlow:        Qt.rgba(102/255,126/255,234/255, 0.10)

    // ── 主布局 ────────────────────────────────────
    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // =========== 左侧：相机画面区域 ============
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 0.65
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                // ── 画面卡片 ──────────────────────
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 16
                    color: cCard
                    border.color: cBorder
                    border.width: 1
                    clip: true

                    Image {
                        id: cameraFeed
                        anchors.fill: parent
                        anchors.margins: 2
                        fillMode: Image.PreserveAspectFit
                        source: "image://camera/live?" + backend.frameCounter
                        cache: false

                        // ── 浮动测量数值（右下） ──
                        Rectangle {
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.margins: 28
                            width: 200
                            height: 120
                            radius: 16
                            color: Qt.rgba(15/255, 17/255, 26/255, 0.78)
                            border.color: Qt.rgba(102/255,126/255,234/255, 0.25)
                            border.width: 1

                            // 外围辉光层
                            Rectangle {
                                z: -1
                                anchors.centerIn: parent
                                width: parent.width + 24
                                height: parent.height + 24
                                radius: 28
                                color: cGlow
                            }

                            Text {
                                id: measureVal
                                anchors.left: parent.left
                                anchors.leftMargin: 22
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.verticalCenterOffset: -6
                                text: backend.measuredDiameter > 0
                                      ? backend.measuredDiameter.toFixed(2) : "--"
                                font.pixelSize: 52
                                font.weight: Font.Light
                                color: cText
                            }

                            Text {
                                anchors.bottom: measureVal.bottom
                                anchors.bottomMargin: 5
                                anchors.left: measureVal.right
                                anchors.leftMargin: 6
                                text: "mm"
                                font.pixelSize: 16
                                color: cTextSec
                            }

                            Text {
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 14
                                anchors.left: parent.left
                                anchors.leftMargin: 22
                                text: "直径"
                                font.pixelSize: 11
                                color: cTextSec
                            }
                        }

                        // ── 文件名水印 ────────────
                        Text {
                            anchors.left: parent.left
                            anchors.bottom: parent.bottom
                            anchors.margins: 20
                            text: backend.currentFile
                            font.pixelSize: 12
                            color: Qt.rgba(255/255,255/255,255/255, 0.3)
                        }
                    }
                }

                // ── 底部状态栏 ────────────────────
                Row {
                    spacing: 20

                    Rectangle {
                        id: dot
                        width: 8; height: 8; radius: 4
                        anchors.verticalCenter: parent.verticalCenter
                        color: backend.statusColor

                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            running: backend.statusText === "分析中..."
                            PropertyAnimation { to: 0.3; duration: 600 }
                            PropertyAnimation { to: 1.0; duration: 600 }
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: backend.statusText
                        font.pixelSize: 13; color: cText
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "帧率: 10fps"
                        font.pixelSize: 13; color: cTextSec
                    }
                }
            }
        }

        // =========== 右侧：控制面板 ============
        Rectangle {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
            radius: 16
            color: cCard
            border.color: cBorder
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18

                // ── 标题 ──────────────────────────
                Text {
                    text: "控制中心"
                    font.pixelSize: 15
                    font.weight: Font.Bold
                    color: cText
                }

                // 分隔线
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: cBorder
                }

                // ── 1. 作业模式 ──────────────────
                Text {
                    text: "作业模式"
                    font.pixelSize: 11; color: cTextSec
                }

                ComboBox {
                    id: modeCombo
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    model: ["螺丝", "螺母垫片", "其他"]
                    currentIndex: 0

                    background: Rectangle {
                        radius: 10
                        color: Qt.rgba(15/255,17/255,26/255, 0.4)
                        border.color: cBorder; border.width: 1
                    }
                    contentItem: Text {
                        leftPadding: 12
                        verticalAlignment: Text.AlignVCenter
                        text: modeCombo.displayText
                        font.pixelSize: 14; color: cText
                    }
                    indicator: Rectangle {
                        x: modeCombo.width - width - 12
                        y: (modeCombo.height - 8) / 2
                        width: 10; height: 8; color: "transparent"
                        Canvas {
                            anchors.fill: parent
                            onPaint: {
                                var ctx = getContext("2d");
                                ctx.fillStyle = "#636e72";
                                ctx.beginPath();
                                ctx.moveTo(0, 0);
                                ctx.lineTo(width / 2, height);
                                ctx.lineTo(width, 0);
                                ctx.closePath();
                                ctx.fill();
                            }
                        }
                    }
                    popup: Popup {
                        y: modeCombo.height + 4
                        width: modeCombo.width
                        padding: 4
                        background: Rectangle {
                            radius: 10; color: "#1a1d2e"
                            border.color: cBorder
                        }
                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: modeCombo.delegateModel
                            currentIndex: modeCombo.currentIndex
                            delegate: ItemDelegate {
                                width: parent.width; height: 36
                                background: Rectangle {
                                    radius: 6
                                    color: modeCombo.currentIndex === index
                                           ? Qt.rgba(102/255,126/255,234/255, 0.2)
                                           : "transparent"
                                }
                                contentItem: Text {
                                    leftPadding: 12
                                    verticalAlignment: Text.AlignVCenter
                                    text: modelData
                                    color: cText; font.pixelSize: 13
                                }
                            }
                        }
                    }
                }

                // ── 2. 系统状态卡 ────────────────
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 74
                    radius: 12
                    color: Qt.rgba(15/255, 17/255, 26/255, 0.4)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 6

                        Row {
                            spacing: 8
                            Rectangle {
                                width: 6; height: 6; radius: 3
                                color: backend.statusColor
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: backend.statusText
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: cText
                            }
                        }
                        Text {
                            text: "当前源: " + backend.currentFile
                            font.pixelSize: 12; color: cTextSec
                        }
                    }
                }

                // ── 3. AI 检测结果卡（预留） ────
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 74
                    radius: 12
                    color: Qt.rgba(15/255, 17/255, 26/255, 0.4)

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 6

                        Row {
                            spacing: 6
                            Text {
                                text: "●  AI"
                                font.pixelSize: 12; font.weight: Font.Bold
                                color: cAccent1
                            }
                            Text {
                                text: "检测结果 (预留)"
                                font.pixelSize: 11; color: cTextSec
                            }
                        }
                        Row {
                            spacing: 24
                            Text {
                                text: "标签: " + backend.aiResultLabel
                                font.pixelSize: 13
                                color: backend.aiResultLabel !== "--"
                                       ? cText : cTextSec
                            }
                            Text {
                                text: "置信度: " + (backend.aiConfidence > 0
                                      ? (backend.aiConfidence * 100).toFixed(1) + "%"
                                      : "--")
                                font.pixelSize: 13
                                color: backend.aiConfidence > 0
                                       ? cText : cTextSec
                            }
                        }
                    }
                }

                // ── 4. 测量值卡（三列：直径/长/宽） ──
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 96
                    radius: 12
                    color: Qt.rgba(15/255, 17/255, 26/255, 0.4)

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6

                        // 直径
                        Item {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            ColumnLayout {
                                anchors.centerIn: parent; spacing: 2
                                Text { text: "直径"; font.pixelSize: 10
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                                Text {
                                    text: backend.measuredDiameter > 0
                                          ? backend.measuredDiameter.toFixed(2) : "--"
                                    font.pixelSize: 28; font.weight: Font.Light
                                    color: backend.measuredDiameter > 0 ? cText : cTextSec
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Text { text: "mm"; font.pixelSize: 11
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                            }
                        }

                        Rectangle {
                            Layout.fillHeight: true; Layout.preferredWidth: 1
                            color: cBorder
                        }

                        // ★ 长度（预留）
                        Item {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            ColumnLayout {
                                anchors.centerIn: parent; spacing: 2
                                Text { text: "长度"; font.pixelSize: 10
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                                Text {
                                    text: backend.measuredLength > 0
                                          ? backend.measuredLength.toFixed(2) : "--"
                                    font.pixelSize: 28; font.weight: Font.Light
                                    color: backend.measuredLength > 0 ? cText : cTextSec
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Text { text: "mm"; font.pixelSize: 11
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                            }
                        }

                        Rectangle {
                            Layout.fillHeight: true; Layout.preferredWidth: 1
                            color: cBorder
                        }

                        // ★ 宽度（预留）
                        Item {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            ColumnLayout {
                                anchors.centerIn: parent; spacing: 2
                                Text { text: "宽度"; font.pixelSize: 10
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                                Text {
                                    text: backend.measuredWidth > 0
                                          ? backend.measuredWidth.toFixed(2) : "--"
                                    font.pixelSize: 28; font.weight: Font.Light
                                    color: backend.measuredWidth > 0 ? cText : cTextSec
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Text { text: "mm"; font.pixelSize: 11
                                    color: cTextSec
                                    Layout.alignment: Qt.AlignHCenter }
                            }
                        }
                    }
                }

                // ── 弹性撑开 ──────────────────────
                Item { Layout.fillHeight: true }

                // ── 5. 按钮组 ─────────────────────

                // 开始分析（渐变主按钮 + 辉光）
                Rectangle {
                    id: btnAnalyze
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    radius: 14
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: cAccent1 }
                        GradientStop { position: 1.0; color: cAccent2 }
                    }

                    Rectangle {
                        z: -1
                        anchors.centerIn: parent
                        width: parent.width + 16; height: parent.height + 16
                        radius: 22
                        color: Qt.rgba(102/255, 126/255, 234/255, 0.12)
                    }

                    Text {
                        anchors.centerIn: parent
                        text: "开始分析"
                        color: "#ffffff"; font.pixelSize: 15; font.weight: Font.Bold
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.startAnalysis()
                        onPressed: parent.opacity = 0.85
                        onReleased: parent.opacity = 1.0
                        onEntered: parent.scale = 1.02
                        onExited: parent.scale = 1.0
                    }
                    Behavior on scale { NumberAnimation { duration: 100 } }
                    Behavior on opacity { NumberAnimation { duration: 80 } }
                }

                // 下一个样本
                Rectangle {
                    id: btnNext
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    radius: 14
                    color: Qt.rgba(255/255,255/255,255/255, 0.03)
                    border.color: cBorder; border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "下一个样本"
                        color: cText; font.pixelSize: 15
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: backend.nextSample()
                        onPressed: parent.color = Qt.rgba(255/255,255/255,255/255, 0.08)
                        onReleased: parent.color = Qt.rgba(255/255,255/255,255/255, 0.03)
                        onEntered: parent.border.color = Qt.rgba(255/255,255/255,255/255, 0.2)
                        onExited: parent.border.color = cBorder
                    }
                }

                // 下达指令
                Rectangle {
                    id: btnCommand
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    radius: 14
                    color: Qt.rgba(255/255,255/255,255/255, 0.03)
                    border.color: cBorder; border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "下达指令"
                        color: cDanger; font.pixelSize: 15
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: backend.sendCommand()
                        onPressed: parent.color = Qt.rgba(255/255,118/255,117/255, 0.08)
                        onReleased: parent.color = Qt.rgba(255/255,255/255,255/255, 0.03)
                        onEntered: parent.border.color = Qt.rgba(255/255,118/255,117/255, 0.3)
                        onExited: parent.border.color = cBorder
                    }
                }
            }
        }
    }
}
