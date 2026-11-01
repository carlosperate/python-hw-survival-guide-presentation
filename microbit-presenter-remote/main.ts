input.onButtonPressed(Button.A, function () {
    keyboard.sendString(keyboard.keys(keyboard._Key.right))
})
let startY = 0
let startX = 0
keyboard.startKeyboardService()
mouse.startMouseService()
basic.forever(function () {
    startX = input.acceleration(Dimension.X)
    startY = input.acceleration(Dimension.Y)
    if (input.buttonIsPressed(Button.B)) {
        keyboard.sendSimultaneousKeys("m", true)
        while (input.buttonIsPressed(Button.B)) {
            // mouse.movexy(input.acceleration(Dimension.Y) / -20, input.acceleration(Dimension.X) / 20)
            mouse.movexy((input.acceleration(Dimension.Y) - startY) / -20, (input.acceleration(Dimension.X) - startX) / 20)
            basic.pause(20)
        }
        keyboard.releaseKeys()
    }
    if (input.logoIsPressed()) {
        while (input.logoIsPressed()) {
            // mouse.movexy(input.acceleration(Dimension.Y) / -20, input.acceleration(Dimension.X) / 20)
            mouse.movexy((input.acceleration(Dimension.Y) - startY) / -20, (input.acceleration(Dimension.X) - startX) / 20)
            basic.pause(20)
        }
    }
})
