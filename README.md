# tileserver-middleman

- show nearby stops/gyms on staticmaps
- hosts staticmaps on discord's cdn
- supports templates, post/get requests, json input, url arg input, multistaticmaps - basically any kind of input your tileserver would also accept
 
if you're considering using this, i'm sure you know how to set this up. below are explained a few extra things to note

instead of filling in your tileserver URL in configs, you use the link to this middleman. (default: `http://127.0.0.1:3031`)

for this to work the tool has to send a request to the middleman and use its response as the image URL. So if the tool is using pregenerate already, it should be easy to implement this.

## Nearby Stops

![](https://media.discordapp.net/attachments/546982390413787136/821835625979183174/unknown.png)

Above is an example for how it would look with [my template](https://gist.github.com/ccev/47b6de2a2f4578a06d14058f323ba0ba). Note that for multistaticmaps, it can only put stops/gyms on the very first map in the list.

To set this up, make sure that your marker list looks something like this:

```js
"markers": [

   /////////////////////////////////

   "#if(middlejson != nil)":"#for(wp in middlejson)":{
      "url":"https://raw.githubusercontent.com/ccev/stopwatcher-icons/master/tileserver-2/#index(wp, 2).png",
      "latitude":"#index(wp",
      0),
      "longitude":"#index(wp",
      1),
      "width":20,
      "height":20,
      "y_offset":-10
   },
   "#endfor
   #endif"
   
   /////////////////////////////////
   
   {
      "url":"https://raw.githubusercontent.com/whitewillem/PogoAssets/resized/icons_large/pokemon_icon_#pad(pokemon_id, 3)_#if(form > 0):#(form)#else:00#endif.png",
      "latitude":"#(latitude)",
      "longitude":"#(longitude)",
      "width":20,
      "height":20
   }
],
```

the part you have to add is marked with `/////`. You need an extra marker below (idealy the pokemon icon), else it will not work.

Now make sure that the request either has `lat/lon` or `latitude/longitude` keys and the `width`, `height` and `zoom` is defined within the template.

and that's it. Templates that don't have this text will be ignored.

