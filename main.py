from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymvp import View, Runnable, Presenter


class Model(object):
    def __init__(self, name):
        self.name = name
        self.presenters = []

    # return data for id here
    def get(self, id):
        raise Exception("not implemented")

    # set data for id here
    def _set(self, id, data):
        raise Exception("not implemented")

    def set(self, id, data):
        self._set(id, data)
        for p in self.presenters:
            p.modelEvent(self, id)


# Transient Dict Model.
class DictModel(Model):
    def __init__(self, name):
        super(DictModel, self).__init__(name)
        self.data = {}

    def get(self, id):
        if id in self.data.keys():
            return self.data[id]
        else:
            return None

    def _set(self, id, data):
        self.data[id] = data


class AppController(Runnable):
    def __init__(self):
        class EventBus(object):
            def __init__(self):
                self.listeners = []

            def register(self, obj):
                self.listeners.append(obj)

            def emit(self, event):
                for listener in self.listeners:
                    listener.receive(event)

        self.bus = EventBus()
        self.bus.register(self)
        self.sm = ScreenManager()
        self.presenters = {}

        bus = self.bus
        sm = self.sm

        class KivyMVPApp(MDApp):
            def build(self):
                return sm

            def on_pause(self):
                for listener in bus.listeners:
                    listener.onPause()

            def on_resume(self):
                for listener in bus.listeners:
                    listener.onResume()

            def on_start(self):
                for listener in bus.listeners:
                    listener.onStart()

            def on_stop(self):
                for listener in bus.listeners:
                    listener.onStop()

        self.app = KivyMVPApp()

    def current(self):
        return self.sm.current

    def switch(self, name):
        self.sm.current = name

    def go(self, first):
        self.sm.current = first
        self.app.run()

    def add(self, pres):
        if pres._name() in self.presenters:
            raise Exception("presenter with name %s exists" % pres._name())
        self.presenters[pres._name()] = pres
        self.bus.register(pres)


if __name__ == '__main__':
    from kivy.graphics import Color, Rectangle
    from kivymd.uix.button import MDRectangleFlatButton
    from kivy.uix.floatlayout import FloatLayout
    from kivymd.uix.label import MDLabel


    # Our app controller simply listens for "switch" events and switches between
    # the two presenters, if it receives one.
    class TestAppController(AppController):
        def receive(self, e):
            if e == "switch":
                for p in self.presenters:
                    if self.current() != p:
                        self.switch(p)
                        break


    ctrl = TestAppController()

    # Our model is a simple dictionary containing a single integer at key 0.
    model = DictModel("aSingleNumber")
    model.set(0, 0)


    # This is a very basic example. Of course we should not duplicate code
    # for such a small difference in functionality. It is just to outline
    # how the framework is intended to be used.

    # The black presenter listens for two user events.
    # If it receives "done" it signals "switch" to the app controller's event bus.
    # (Note: all presenters and the app controller are registered at the event bus
    #  and can response to events if required)
    # If it receives an "add" event it retrieves the current number from the model,
    # increments by one and puts it back into the model.
    # On receiving any event from the model it simply retrieves the currently stored
    # number and instructs the view to update based on it.
    class BlackPresenter(Presenter):
        def _name(self):
            return "black"

        def userEvent(self, e):
            if e == "done":
                self.emit("switch")
            elif e == "add":
                x = self.models["aSingleNumber"].get(0)
                self.models["aSingleNumber"].set(0, x + 1)

        def modelEvent(self, m, e=None):
            self.view.update(str(m.get(0)))


    # The white presenter listens for two user events.
    # If it receives "done" it signals "switch" to the app controller's event bus.
    # If it receives an "subtract" event it retrieves the current number from the model,
    # decrements by one and puts it back into the model.
    # On receiving any event from the model it simply retrieves the currently stored
    # number and instructs the view to update based on it.
    class WhitePresenter(Presenter):
        def _name(self):
            return "white"

        def userEvent(self, e):
            if e == "done":
                self.emit("switch")
            elif e == "subtract":
                x = self.models["aSingleNumber"].get(0)
                self.models["aSingleNumber"].set(0, x - 1)

        def modelEvent(self, m, e=None):
            self.view.update(str(m.get(0)))


    # This is just a simple layout with a background color such that we can easily
    # distinguish our two views.
    class ColorLayout(FloatLayout):
        def __init__(self, color, **kwargs):
            super(ColorLayout, self).__init__(**kwargs)
            with self.canvas.before:
                Color(color[0], color[1], color[2], color[3])
                self.rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

        def _update_rect(self, instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size


    # The black view has a button "add" and a button "to_white" on a black background.
    # Pressing "add" triggers emits the event "add" and pressing "to white" triggers "done".
    # When it receives an update event it updates the label text with the new data.
    # Note that all kivy events should just trigger self.event with the appropriate data to
    # integrate into the MVP workflow.
    class BlackView(View):
        def __init__(self, presenter, **kwargs):
            super(BlackView, self).__init__(presenter, **kwargs)
            with self.canvas:
                f = ColorLayout((1, 1, 0, 1))
                self.l = MDLabel(text="TEST", size_hint=(1, 0.25), pos_hint={"x": 0, "y": 0.8},
                                 font_size=60)
                f.add_widget(self.l)
                b = MDRectangleFlatButton(text='add', font_size=20,
                                          pos_hint={"x": 0, "y": 0.25})
                b.bind(on_press=lambda x: self.event("add"))
                f.add_widget(b)
                b = MDRectangleFlatButton(text='to white', font_size=20)
                b.bind(on_press=lambda x: self.event("done"))
                f.add_widget(b)
                self.add_widget(f)

        def _update(self, data):
            self.l.text = data


    # The white view has a button "add" and a button "to_black" on a white background.
    # Pressing "add" triggers emits the event "add" and pressing "to black" triggers "done".
    # When it receives an update event it updates the label text with the new data.
    class WhiteView(View):
        def __init__(self, presenter, **kwargs):
            super(WhiteView, self).__init__(presenter, **kwargs)
            with self.canvas:
                f = ColorLayout((1, 1, 1, 1))
                self.l = MDLabel(text="TEST", size_hint=(1, 0.25), pos_hint={"x": 0, "y": 0.8},
                                 color=(0.75, 0.75, 0.75, 1), font_size=60)
                f.add_widget(self.l)
                b = MDRectangleFlatButton(text='subtract', font_size=20, size_hint=(1, 0.25),
                                          pos_hint={"x": 0, "y": 0.25})
                b.bind(on_press=lambda x: self.event("subtract"))
                f.add_widget(b)
                b = MDRectangleFlatButton(text='to black', font_size=20, size_hint=(1, 0.25))
                b.bind(on_press=lambda x: self.event("done"))
                f.add_widget(b)
                self.add_widget(f)

        def _update(self, data):
            self.l.text = data


    black_pres = BlackPresenter(ctrl, BlackView, [model])
    white_pres = WhitePresenter(ctrl, WhiteView, [model])

    ctrl.add(white_pres)
    ctrl.add(black_pres)

    # Start black.
    ctrl.go('black')
