# import all the relevant classes
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.checkbox import CheckBox
from kivy.event import EventDispatcher
from jnius import autoclass
import mysql.connector
from mysql.connector.constants import ClientFlag
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior

# DATABASE CONFIGUATION
config = {
    'user': '',
    'password': '',
    'host': '',
    'database': ''
}

cxn = mysql.connector.connect(**config)
cursor = cxn.cursor()

'''
# Bluetooth socket information
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')
String = autoclass("java.lang.String")
CharBuilder = autoclass('java.lang.Character')

# Connect and return bluetooth socket
def get_socket_stream(name):
    paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
    socket = None
    for device in paired_devices:
        if device.getName() == name:
            socket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
            recv_stream = socket.getInputStream()
            send_stream = socket.getOutputStream()
            break
    socket.connect()
    return recv_stream, send_stream

# Connecting to bluetooth stream
recv_stream, send_stream = get_socket_stream('HC-05')

# Send to bluetooth
def send(cmd):
    msg = '{}'.format(cmd)
    bytes = [ord(c) for c in msg]
    send_stream.write(bytes)
    #self.send_stream.flush()
    
# Receive from bluetooth
def receive():
    msg = ''
    msg = str(recv_stream.readline())
    return msg

'''

class TextInputPopup(Popup):
    obj = ObjectProperty(None)
    obj_text = StringProperty("")

    def __init__(self, obj, **kwargs):
        super(TextInputPopup, self).__init__(**kwargs)
        self.obj = obj
        self.obj_text = obj.text


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableButton(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableButton, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected


    def on_press(self):
        popup = TextInputPopup(self)
        popup.open()

    def update_changes(self, txt):
        self.text = txt
        print(self.index)



class RV(BoxLayout):
    data_items = ListProperty([])

    def get_users(self):
        cursor.execute("SELECT * FROM patrons")
        rows = cursor.fetchall()

        # create data_items
        for row in rows:
            for col in row:
                if(col == 0.73):
                    self.data_items.append('Male')
                elif(col == 0.66):
                    self.data_items.append("Female")
                else:
                    self.data_items.append(col)

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.get_users()


# Class for main window
class mainWindow(Screen):
    pass

# Class for create user window
class createWindow(Screen):
    uniqueID = ObjectProperty(None)
    priorDrinks = ObjectProperty(None)
    elapsed = ObjectProperty(None)
    weight = ObjectProperty(None)
    gcost = 0

    # If female is selected, gender constant is 0.66
    def femalesel(self,active):
        if(active):
            self.gcost = 0.66

    # If male selected, gender constant is 0.73
    def malesel(self,active):
        if(active):
            self.gcost = 0.73

    def initializeUser(self):

        weight = int(self.weight.text)
        gender = self.gcost

        BAC = ( (0.6*float(self.priorDrinks.text)) * 5.14 / (weight * gender) )
        cursor.execute('INSERT INTO patrons (id, drinks, time, weight, gender, bac) VALUES (%s,%s,%s,%s,%s,%s)', (self.uniqueID.text,float(self.priorDrinks.text),int(self.elapsed.text),weight,gender,BAC) )
        cxn.commit()
        # BAC colors for male (https://safeparty.ucdavis.edu/watch-your-bac)
        # Gold zone is green (0 - 0.07)
        # Orange zone is yellow (0.08 - 0.15)
        # Red zone is red (0.15+)
        '''
         if (BAC <= 0.07):
            send('1')
        elif (BAC >= 0.08 and BAC <= 0.15):
            send('2')
        else:
            send('3')
'''
# Class for see users window
class seeWindow(Screen):
    pass

# Class for delete users window
class deleteWindow(Screen):
    pass

# Class for update user window
class updateWindow(Screen):
    uniqueID = ObjectProperty(None)
    drinks = ObjectProperty(None)
    time_M = ObjectProperty(None)

    def updateUser(self):
        gender = 0
        BAC = 0
        elapsed = 0
        weight = 0
        time_last = 0

        # If this is their first drink use elapsed since their prior drinks
        if(time_last == 0):
            BAC += ((0.6 * float(self.drinks.text)) * 5.14 / (weight * gender))
            time_last = int(self.time_M.text)

        # If this is a subsequent drink
        else:
            if( int(self.time_M.text) >= time_last):
                BAC += (((0.6 * float(self.drinks.text)) * 5.14 / (weight * gender)) - (0.015 * (int(self.time_M.text)-time_last)))
                time_last = int(self.time_M.text)
            else:
                BAC += (((0.6 * float(self.drinks.text)) * 5.14 / (weight * gender)) - (0.015 * (time_last - int(self.time_M.text) )))
                time_last = int(self.time_M.text)



        # BAC colors for male (https://safeparty.ucdavis.edu/watch-your-bac)
        # Gold zone is green (0 - 0.07)
        # Orange zone is yellow (0.08 - 0.15)
        # Red zone is red (0.15+)
        '''
        if (BAC <= 0.07):
            send('1')
        elif (BAC >= 0.08 and BAC <= 0.15):
            send('2')
        else:
            send('3')
'''
# Class for managing windows
class windowManager(ScreenManager):
    pass

# Bringing in gui file
kv = Builder.load_file('gui.kv')
pgm = windowManager()

# Adding Windows
pgm.add_widget(mainWindow(name='mainW'))
pgm.add_widget(createWindow(name='createW'))
pgm.add_widget(seeWindow(name='seeW'))
pgm.add_widget(deleteWindow(name='deleteW'))
pgm.add_widget(updateWindow(name='updateW'))

# Builds the GUI
class MainApp(App):
    def build(self):
        return pgm

if __name__=="__main__":
    MainApp().run()

