import discord
from typing import List
from collections import deque

class PaginatorView(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed]) -> None:
        super().__init__(timeout=30)

        self._embeds = embeds
        self._queue = deque(embeds)
        self._initial = embeds[0]
        self._len = len(embeds)
        self._current_page = 1


    @discord.ui.button(label="<-")
    async def previous(self, interaction: discord.Integration, _):
        self._queue.rotate(-1)
        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="->")
    async def previous(self, interaction: discord.Integration, _):
        self._queue.rotate(1)
        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial
