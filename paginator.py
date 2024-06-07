import discord
from typing import List
from collections import deque

class PaginatorView(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed]) -> None:
        super().__init__(timeout=60)

        self._embeds = embeds
        self._queue = deque(embeds)
        self._initial = embeds[0]
        self._len = len(embeds)
        self._current_page = 1
        self.children[0].disabled = True
        self._queue[0].set_footer(text=f"{self._current_page}/{self._len}")


    async def update_buttons(self, interaction: discord.Interaction) -> None:
        for i in self._queue:
            i.set_footer(text=f"{self._current_page}/{self._len}")
        if self._current_page == self._len:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False

        if self._current_page == 1:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        await interaction.message.edit(view=self)


    @discord.ui.button(label="<-")
    async def previous(self, interaction: discord.Integration, _):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self._current_page -= 1
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="->")
    async def next(self, interaction: discord.Integration, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        self._current_page += 1
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial
