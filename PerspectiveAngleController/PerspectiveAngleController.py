# Fusion360API Python Addin
import adsk.core
import adsk.fusion
import traceback
import json
import math

handlers = []
_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None

_cmdInfo = {
    'id': 'PerspectiveAngleControllerCmd',
    'name': '視点角度を調整',
    'tooltip': '視点角度を調整する',
    'resources': ''
}

_paletteInfo = {
    'id': 'PerspectiveAngleControllerPalette',
    'name': _cmdInfo["name"],
    'htmlFileURL': 'index.html',
    'isVisible': True,
    'showCloseButton': True,
    'isResizable': True,
    'width': 300,
    'height': 180,
    'useNewWebBrowser': False,  # True,
    'dockingState': None
}

_perspectiveAngle = 0.1

_CAMERA_TYPES = {
    'OrthographicCameraType': adsk.core.CameraTypes.OrthographicCameraType,
    'PerspectiveCameraType': adsk.core.CameraTypes.PerspectiveCameraType,
}


def updatePerspectiveAngle():
    try:
        global _perspectiveAngle
        app: adsk.core.Application = adsk.core.Application.get()
        vp: adsk.core.Viewport = app.activeViewport
        cam: adsk.core.Camera = vp.camera
        cam.perspectiveAngle = _perspectiveAngle
        cam.isFitView = False
        cam.isSmoothTransition = False
        vp.camera = cam
        vp.refresh()
    except:
        pass


class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            htmlArgs = adsk.core.HTMLEventArgs.cast(args)

            app: adsk.core.Application = adsk.core.Application.get()
            vp: adsk.core.Viewport = app.activeViewport
            cam: adsk.core.Camera = vp.camera

            global _app, _CAMERA_TYPES
            if htmlArgs.action == 'htmlLoaded':
                args.returnData = json.dumps({
                    'action': 'send',
                    'perspectiveAngle': str(math.degrees(cam.perspectiveAngle)),
                    'cameraType': cam.cameraType,
                })
                # dumpCameraInfo()

            elif htmlArgs.action == 'sliderChange':
                data = json.loads(htmlArgs.data)

                global _perspectiveAngle
                _perspectiveAngle = math.radians(int(data['value']))

                updatePerspectiveAngle()

            elif htmlArgs.action == 'typeChange':
                data = json.loads(htmlArgs.data)
                # app.log(data['value'])

                global _CAMERA_TYPES
                cameraType = _CAMERA_TYPES[data['value']]

                if cam.cameraType == cameraType:
                    return

                cam.cameraType = cameraType
                vp.camera = cam

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class ShowPaletteCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            global _ui, _paletteInfo

            palette = _ui.palettes.itemById(_paletteInfo['id'])
            if palette:
                palette.deleteMe()

            palette = _ui.palettes.add(
                _paletteInfo['id'],
                _paletteInfo['name'],
                _paletteInfo['htmlFileURL'],
                _paletteInfo['isVisible'],
                _paletteInfo['showCloseButton'],
                _paletteInfo['isResizable'],
                _paletteInfo['width'],
                _paletteInfo['height'],
                _paletteInfo['useNewWebBrowser'],
            )

            if _paletteInfo['dockingState']:
                palette.dockingState = _paletteInfo['dockingState']
            else:
                palette.setPosition(800, 400)

            onHTMLEvent = MyHTMLEventHandler()
            palette.incomingFromHTML.add(onHTMLEvent)
            handlers.append(onHTMLEvent)

            onClosed = MyCloseEventHandler()
            palette.closed.add(onClosed)
            handlers.append(onClosed)

        except:
            _ui.messageBox('Command executed failed: {}'.format(
                traceback.format_exc()))


class MyCloseEventHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            pass
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class ShowPaletteCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.command
            onExecute = ShowPaletteCommandExecuteHandler()
            command.execute.add(onExecute)
            handlers.append(onExecute)
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        global _ui, _app
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        global _cmdInfo
        showPaletteCmdDef = _ui.commandDefinitions.itemById(_cmdInfo['id'])
        if showPaletteCmdDef:
            showPaletteCmdDef.deleteMe()

        showPaletteCmdDef = _ui.commandDefinitions.addButtonDefinition(
            _cmdInfo['id'],
            _cmdInfo['name'],
            _cmdInfo['tooltip'],
            _cmdInfo['resources']
        )

        onCommandCreated = ShowPaletteCommandCreatedHandler()
        showPaletteCmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        panel = _ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cntrl = panel.controls.itemById('showPalette')
        if not cntrl:
            panel.controls.addCommand(showPaletteCmdDef)

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        global _paletteInfo
        palette = _ui.palettes.itemById(_paletteInfo['id'])
        if palette:
            palette.deleteMe()

        global _cmdInfo
        panel = _ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cmd = panel.controls.itemById(_cmdInfo['id'])
        if cmd:
            cmd.deleteMe()
        cmdDef = _ui.commandDefinitions.itemById(_cmdInfo['id'])
        if cmdDef:
            cmdDef.deleteMe()

        _app.log('Stop addin')
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# ** debug **
def dumpCameraInfo():
    app: adsk.core.Application = adsk.core.Application.get()
    vp: adsk.core.Viewport = app.activeViewport
    cam: adsk.core.Camera = vp.camera

    length = cam.eye.distanceTo(cam.target)
    global _CAMERA_TYPES
    camTypes = list(_CAMERA_TYPES.keys())

    msg = '- camera info -\n'
    msg += f'type:{cam.cameraType} - {camTypes[cam.cameraType]}\n'
    msg += f'perspectiveAngle:{cam.perspectiveAngle}\n'
    msg += f'viewExtents:{cam.viewExtents}\n'
    msg += f'length:{length}\n'
    msg += f'eye:{cam.eye.x},{cam.eye.y},{cam.eye.z}\n'
    msg += f'target:{cam.target.x},{cam.target.y},{cam.target.z}\n'

    app.log(msg)
