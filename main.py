import threading
import json
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class NexusBetRoot(BoxLayout):
    def __init__(self, **kwargs):
        super(NexusBetRoot, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 25
        self.spacing = 15

        self.add_widget(Label(text='Nexus-Bet (Quantum + Football)', font_size=20, size_hint_y=None, height=40))

        self.add_widget(Label(text='Token IBM Quantum:', size_hint_y=None, height=25))
        self.ibm_token_input = TextInput(
            text='mPIg_rIpBe1HwmLKw1onL7-RZwYtCswqCxYBKhbqUbzB',
            multiline=False, size_hint_y=None, height=40
        )
        self.add_widget(self.ibm_token_input)

        self.status_label = Label(text='Status: Pronto', font_size=13)
        self.add_widget(self.status_label)

        self.btn_calc = Button(text='Executar Otimização Quântica', size_hint_y=None, height=55)
        self.add_widget(self.btn_calc)

class NexusBetApp(App):
    def build(self):
        return NexusBetRoot()

if __name__ == '__main__':
    NexusBetApp().run()
