# tileserver-middleman

- show nearby stops/gyms on staticmaps
- hosts staticmaps on discord's cdn: faster loading & hiding your url
- supports templates, post/get requests, json input, url arg input, multistaticmaps - basically any kind of input your tileserver would also accept
 
if you're considering using this, i'm sure you know how to set this up. just read the rest of the readme

instead of filling in your tileserver URL in other tool configs, you use the link to this middleman. (default: `http://127.0.0.1:3031`)

for this to work the tool has to send a request to the middleman and use its response as the image URL. So if the tool is using pregenerate already, it should be easy to implement this.

You can define a list of webhooks the script will cycle through. Usually one is enough but you can set multiple if you want.

## Nearby Stops

![](https://media.discordapp.net/attachments/546982390413787136/821835625979183174/unknown.png)

Above is an example for how it would look with [my template](https://gist.github.com/ccev/47b6de2a2f4578a06d14058f323ba0ba). Note that for multistaticmaps, it can only put stops/gyms on the very first map in the list.

To set this up, make sure that your marker list looks something like this:

```js
"markers": [

   /////////////////////////////////

   #if(middlejson != nil):
   #for(wp in middlejson):
   {
      "url": "https://raw.githubusercontent.com/ccev/stopwatcher-icons/master/tileserver-2/#index(wp, 2).png",
      "latitude": #index(wp, 0),
      "longitude": #index(wp, 1),
      "width": 20,
      "height": 20,
      "y_offset": -10
   },
   #endfor
   #endif
   
   /////////////////////////////////
   
   {
      "url": "https://raw.githubusercontent.com/whitewillem/PogoAssets/resized/icons_large/pokemon_icon_#pad(pokemon_id, 3)_#if(form > 0):#(form)#else:00#endif.png",
      "latitude": #(latitude),
      "longitude": #(longitude),
      "width": 20,
      "height": 20
   }
],
```

the part you have to add is marked with `/////`. You need an extra marker below (ideally the pokemon icon), else it will not work.

Now make sure that the request either has `lat/lon` or `latitude/longitude` keys and `width`, `height` and `zoom` are defined within the template.

and that's it. Templates that don't have this text will be ignored and just get hosted on discord.

you can set a custom height/width for the stop/gym markers and adjust it to your template. just make sure that y_offset is half of that. You can also use your own icons by changing the url and have the file structure there look like [this](https://github.com/ccev/stopwatcher-icons/tree/master/tileserver-2)

