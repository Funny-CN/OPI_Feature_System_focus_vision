print("hello")
import os

filepath = r"D:\python\Python_Projects\OPI_Feature_System_focus_vision\ui\VisionUI.qml"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Fix x coordinates of the three bars (8->12, 14->18, 20->24)
content = content.replace(
    'Rectangle { x: 8; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 12; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)
content = content.replace(
    'Rectangle { x: 14; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 18; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)
content = content.replace(
    'Rectangle { x: 20; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 24; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)

# Step 2: Replace root RowLayout with ColumnLayout
# Find the old root layout boundary
marker = '    RowLayout {\n        anchors.fill: parent; anchors.margins: 20; spacing: 14\n        Item {\n            Layout.preferredWidth: 60; Layout.fillHeight: true'
idx = content.find(marker)
print(f"Found root at idx={idx}")
assert idx != -1, "Could not find root RowLayout"

# Find matching close brace (depth counting)
depth = 0
end_idx = idx
for i in range(idx, len(content)):
    if content[i] == '{':
        depth += 1
    elif content[i] == '}':
        depth -= 1
    if depth == 0:
        end_idx = i + 1
        break

print(f"Root extends from {idx} to {end_idx}")
old_root = content[idx:end_idx]

# Build the new ColumnLayout root
indent = '    '
new_root = indent + 'ColumnLayout {\n'
new_root += indent + '    anchors.fill: parent; anchors.margins: 20; spacing: 14\n'
new_root += indent + '    Rectangle {\n'
new_root += indent + '        Layout.fillWidth: true; Layout.preferredHeight: 48; radius: cRadiusSm\n'
new_root += indent + '        color: Qt.rgba(20/255,28/255,47/255,0.25)\n'
new_root += indent + '        border.color: Qt.rgba(180/255,80/255,255/255,0.12); border.width: 1\n'
new_root += indent + '        RowLayout {\n'
new_root += indent + '            anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16\n'
new_root += indent + '            Row { spacing: 10\n'
new_root += indent + '                Rectangle { width: 8; height: 8; radius: 4; color: cCyan; anchors.verticalCenter: parent.verticalCenter\n'
new_root += indent + '                    SequentialAnimation on opacity { loops: Animation.Infinite\n'
new_root += indent + '                        PropertyAnimation { to: 0.3; duration: 1200 }\n'
new_root += indent + '                        PropertyAnimation { to: 1.0; duration: 1200 } } }\n'
new_root += indent + '                Text { text: "VisionFlow"; font.pixelSize: 15; font.weight: Font.Bold; color: cCyan }\n'
new_root += indent + '                Text { text: "| \u89c6\u89c9\u667a\u80fd\u7b5b\u9009\u7cfb\u7edf"; font.pixelSize: 15; font.weight: Font.Bold; color: cTextWhite }\n'
new_root += indent + '            }\n'
new_root += indent + '            Item { Layout.fillWidth: true }\n'
new_root += indent + '            Row { spacing: 16\n'
new_root += indent + '                Row { spacing: 6\n'
new_root += indent + '                    Rectangle { width: 6; height: 6; radius: 3; color: cGreen; anchors.verticalCenter: parent.verticalCenter }\n'
new_root += indent + '                    Text { text: "\u7cfb\u7edf\u6b63\u5e38"; font.pixelSize: 12; color: cTextSec }\n'
new_root += indent + '                }\n'
new_root += indent + '                Rectangle { width: 1; height: 18; color: Qt.rgba(255/255,255/255,255/255,0.06) }\n'
new_root += indent + '                Text { text: "\u5e27\u7387: 10fps"; font.pixelSize: 12; color: cTextSec }\n'
new_root += indent + '            }\n'
new_root += indent + '        }\n'
new_root += indent + '    }\n'
new_root += indent + '    RowLayout {\n'
new_root += indent + '        Layout.fillWidth: true; Layout.fillHeight: true; spacing: 14\n'

# Extract the sidebar Item and StackLayout from the old root
# Old structure: RowLayout > Item(sidebar) + ColumnLayout(Rect(topbar) + StackLayout)
# New structure: ColumnLayout > Rectangle(topbar) + RowLayout(Item(sidebar) + StackLayout)
# We need to extract the sidebar Item and StackLayout from the old root

# Find the sidebar Item (old root's first child)
sidebar_marker = '        Item {\n            Layout.preferredWidth: 60; Layout.fillHeight: true\n            Rectangle {'
sidx = old_root.find(sidebar_marker)
assert sidx != -1, "Could not find sidebar"

# Find where sidebar Item ends - find its closing brace
depth_side = 0
side_end = sidx
for i in range(sidx, len(old_root)):
    if old_root[i] == '{':
        depth_side += 1
    elif old_root[i] == '}':
        depth_side -= 1
    if depth_side == 0:
        side_end = i + 1
        break

sidebar_content = old_root[sidx:side_end]
print(f"Sidebar content: {sidebar_content[:50]}...")

# Remove the old root and insert the sidebar content in the new structure
new_root += indent + sidebar_content + '\n'
new_root += indent + '            StackLayout {\n'

# Find the StackLayout in the old root (it's inside ColumnLayout > StackLayout)
stack_marker = '            StackLayout {\n                Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: currentPage'
stack_idx = old_root.find(stack_marker)
assert stack_idx != -1, f"Could not find StackLayout (found at {stack_idx})"

depth_stk = 0
stk_end = stack_idx
for i in range(stack_idx, len(old_root)):
    if old_root[i] == '{':
        depth_stk += 1
    elif old_root[i] == '}':
        depth_stk -= 1
    if depth_stk == 0:
        stk_end = i + 1
        break

stack_content = old_root[stack_idx:stk_end]
print(f"StackLayout content: {stack_content[:50]}...")

# Close the new root
new_root += indent + '            }\n'  # close StackLayout
new_root += indent + '        }\n'  # close RowLayout
new_root += indent + '    }\n'  # close ColumnLayout

content = content[:idx] + new_root + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! Applied ColumnLayout restructuring and x coordinate fixes.")
filepath = r"D:\python\Python_Projects\OPI_Feature_System_focus_vision\ui\VisionUI.qml"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix x coordinates of the three bars (8->12, 14->18, 20->24)
content = content.replace(
    'Rectangle { x: 8; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 12; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)
content = content.replace(
    'Rectangle { x: 14; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 18; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)
content = content.replace(
    'Rectangle { x: 20; y: 10; width: 4; height: 20; radius: 1; color: cCyan',
    'Rectangle { x: 24; y: 10; width: 4; height: 20; radius: 1; color: cCyan'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! X coordinates fixed: 8->12, 14->18, 20->24")
