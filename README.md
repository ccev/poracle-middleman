# tileserver-middleman
 
if you're considering using this, i'm sure you know how to set this up. nothing special.

instead of filling in your tileserver URL in configs, you use the link to this middleman. (default: `http://127.0.0.1:3031`)

for this to work the tool has to send a request to the middleman and use its response as the image URL. So if the tool is using pregenerate already, it should be easy to implement this.

very little tested. works with poracle.
