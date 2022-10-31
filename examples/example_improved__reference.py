import flet
from flet import Column, ElevatedButton, Text, TextField
from flet_improvements.ref import Ref

def main(page):

    first_name = Ref[TextField]()
    last_name = Ref[TextField]()
    greetings = Ref[Column]()

    def btn_click(e):
        greetings().controls.append(
            Text(f'Hello, {first_name().value} {last_name().value}!')
        )
        first_name().value = ''
        last_name().value = ''
        first_name().focus()
        page.update()

    page.add(
        TextField(ref=first_name, label='First name', autofocus=True),
        TextField(ref=last_name, label='Last name'),
        ElevatedButton('Say hello!', on_click=btn_click),
        Column(ref=greetings),
    )

flet.app(target=main)
