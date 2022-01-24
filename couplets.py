# -*- coding:utf-8 -*-
# @author Python 集中营
# @date 2022/1/18
# @file test4.py

# 需求说明：
# 通过在界面上输入春联的上、下批和横批汉字从而生成春联图像，最后将春联图片保存。有实际需要的还可以将春联打印。
#
# 实现过程：
# 实现思路是先下载好春联的背景图片，再下载每个汉字的文字图片将文字图片粘贴到春联背景上。所以这里有用了一个春联图片的三方获取地址。
# http://xufive.sdysit.com/tk
# 春联生成部分参考了 CSDN 博客平台

'''网络数据获取相关模块'''
import io  # python IO 处理模块
from PIL import Image  # 图像处理模块
import requests  # 网络请求模块

'''UI 相关模块'''
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 主题样式模块引用
from QCandyUi import CandyWindow

'''应用操作相关模块'''
import sys
import os


class WorkThread(QThread):
    trigger = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(WorkThread, self).__init__(parent)
        self.parent = parent
        self.working = True

    def __del__(self):
        self.working = False
        self.wait()

    def run(self):
        up_text = self.parent.up_text.text().strip()
        down_text = self.parent.down_text.text().strip()
        h_text = self.parent.h_text.text().strip()
        save_path = self.parent.save_path.text().strip()
        if up_text == '' or down_text == '' or h_text == '' or save_path == '':
            self.trigger.emit('参数设置不允许为空，请设置好后重新开始！')
            self.finished.emit(True)
        else:
            text = up_text + ' ' + down_text
            self.generate_image(text, layout='V', pre=0.75, out_file=save_path + '/上下联.jpg')
            self.generate_image(h_text, layout='H', pre=0.75, out_file=save_path + '/横批.jpg')
            self.finished.emit(True)

    def get_word_image(self, ch='bg', pre=1.0):
        '''
        单文字图片下载函数
        :param ch: 默认网络请求参数'bg'
        :param pre: 单个文字对象
        :return: 图像对象
        '''
        res = io.BytesIO(requests.post(url='http://xufive.sdysit.com/tk', data={'ch': ch}).content)
        image = Image.open(res)
        w, h = image.size
        w, h = int(w * float(pre)), int(h * float(pre))
        return image.resize((w, h))  # 单个文字的形状是正方形，所以这里的长、宽都是一致的

    def generate_image(self, words, layout='V', pre=1.0, out_file=None):
        '''
        春联生成函数
        :param words: 春联文本
        :param layout: 布局：水平/垂直
        :param pre: 春联比例
        :param out_file: 保存文件
        :return:
        '''
        quality = 'H'
        if pre == 0.75:
            quality = 'M'
        elif pre == 0.5:
            quality = 'L'
        usize = {'H': (640, 23), 'M': (480, 18), 'L': (320, 12)}
        bg_im = self.get_word_image(ch='bg', pre=pre)
        self.trigger.emit('春联背景下载完成！')
        text_list = [list(item) for item in words.split()]
        rows = len(text_list)
        cols = max([len(item) for item in text_list])

        if layout == 'V':
            ow, oh = 40 + rows * usize[quality][0] + (rows - 1) * 10, 40 + cols * usize[quality][0]
        else:
            ow, oh = 40 + cols * usize[quality][0], 40 + rows * usize[quality][0] + (rows - 1) * 10
        out_im = Image.new('RGBA', (ow, oh), '#f0f0f0')

        for row in range(rows):
            if layout == 'V':
                row_im = Image.new('RGBA', (usize[quality][0], cols * usize[quality][0]), 'white')
                offset = (ow - (usize[quality][0] + 10) * (row + 1) - 10, 20)
            else:
                row_im = Image.new('RGBA', (cols * usize[quality][0], usize[quality][0]), 'white')
                offset = (20, 20 + (usize[quality][0] + 10) * row)

            for col, ch in enumerate(text_list[row]):
                if layout == 'V':
                    pos = (0, col * usize[quality][0])
                else:
                    pos = (col * usize[quality][0], 0)
                ch_im = self.get_word_image(ch=ch, pre=pre)
                row_im.paste(bg_im, pos)
                row_im.paste(ch_im, (pos[0] + usize[quality][1], pos[1] + usize[quality][1]), mask=ch_im)

            out_im.paste(row_im, offset)
        self.trigger.emit('春联图片拼装完成！')

        if out_file:
            out_im.convert('RGB').save(out_file)
            self.trigger.emit('春联保存成功！')


class GenerateScroll(QWidget):
    def __init__(self):
        super(GenerateScroll, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('瓜子春联')
        self.setWindowIcon(QIcon('春联.ico'))

        vbox_main = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setScaledContents(True)
        self.image_label.setMaximumSize(650,150)
        self.image_label.setPixmap(QPixmap('横批演示.jpg'))

        hbox = QHBoxLayout()
        self.brower = QTextBrowser()
        self.brower.setFont(QFont('宋体', 8))
        self.brower.setReadOnly(True)
        self.brower.setPlaceholderText('信息展示区域')
        self.brower.ensureCursorVisible()

        form = QFormLayout()

        self.up_label = QLabel()
        self.up_label.setText('设置上联')

        self.up_text = QLineEdit()
        self.up_text.setPlaceholderText('请输入上联')

        self.down_label = QLabel()
        self.down_label.setText('设置下联')

        self.down_text = QLineEdit()
        self.down_text.setPlaceholderText('请输入下联')

        self.h_label = QLabel()
        self.h_label.setText('设置横批')

        self.h_text = QLineEdit()
        self.h_text.setPlaceholderText('请输入横批')

        self.thread_ = WorkThread(self)
        self.thread_.trigger.connect(self.update_log)
        self.thread_.finished.connect(self.finished)

        self.save_path = QLineEdit()
        self.save_path.setReadOnly(True)

        self.save_btn = QPushButton()
        self.save_btn.setText('存储路径')
        self.save_btn.clicked.connect(self.save_btn_click)

        form.addRow(self.up_label, self.up_text)
        form.addRow(self.down_label, self.down_text)
        form.addRow(self.h_label, self.h_text)
        form.addRow(self.save_path, self.save_btn)

        vbox = QVBoxLayout()

        self.start_btn = QPushButton()
        self.start_btn.setText('开始生成春联')
        self.start_btn.clicked.connect(self.start_btn_click)

        vbox.addLayout(form)
        vbox.addWidget(self.start_btn)

        hbox.addWidget(self.brower)
        hbox.addLayout(vbox)

        vbox_main.addWidget(self.image_label)
        vbox_main.addLayout(hbox)

        self.setLayout(vbox_main)

    def update_log(self, text):
        '''
        槽函数：向文本浏览器中写入内容
        :param text:
        :return:
        '''
        cursor = self.brower.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.brower.append(text)
        self.brower.setTextCursor(cursor)
        self.brower.ensureCursorVisible()

    def save_btn_click(self):
        dicr = QFileDialog.getExistingDirectory(self, '选择文件夹', os.getcwd())
        self.save_path.setText(dicr)

    def start_btn_click(self):
        self.start_btn.setEnabled(False)
        self.thread_.start()

    def finished(self, finished):
        if finished is True:
            self.start_btn.setEnabled(True)
            h_image = self.save_path.text().strip() + '/横批.jpg'
            if os.path.isfile(h_image):
                self.image_label.setPixmap(QPixmap(h_image))
            self.update_log('由于上下联不好预览，请使用图片查看器预览，目前仅支持横批图片预览...')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CandyWindow.createWindow(GenerateScroll(), theme='blue', title='瓜子春联',
                                 ico_path='春联.ico')
    w.show()
    sys.exit(app.exec_())
