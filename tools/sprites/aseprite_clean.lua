-- Aseprite (built from source for our own use; its EULA forbids sharing the binary, so it is not in the repo), batch:
--   aseprite -b --script-param input=sage_x3.png --script-param palette=ours.gpl --script-param despeckle=0 \
--            --script-param output=out.png --script tools/sprites/aseprite_clean.lua
-- input: a render three times the sprite's size, no outline; palette: a GIMP .gpl of the body's material ramps.
-- the render, three times too big, brought to the sprite's size by Aseprite's own means:
-- RotSprite (keeps pixel lines whole), optionally a median despeckle, our palette without dither, an outline
local spr = app.open(app.params.input)
app.command.SpriteSize{ ui=false, scale=1/3, method="rotsprite" }
if app.params.despeckle == "1" then
  app.command.Despeckle{ ui=false, width=3, height=3 }
end
local pal = Palette{ fromFile = app.params.palette }
spr:setPalette(pal)
app.command.ChangePixelFormat{ ui=false, format="indexed", dithering="none" }
app.command.ChangePixelFormat{ ui=false, format="rgb" }
app.command.Outline{ ui=false, color=Color{ r=12, g=10, b=16, a=255 }, matrix="circle", place="outside" }
spr:saveCopyAs(app.params.output)
