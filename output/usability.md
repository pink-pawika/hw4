# Usability improvements

Four changes. Two are on the website. Two are tools the shop assistant calls. Each one is visible in the running app.

## 1. Filters on the rack

**What I added.** The products page has buttons: All, Hoodies, T-shirts, Crewnecks, Jackets, and More. Each button shows how many pieces are in that group. Hoodies include pullover hoodies and hooded sweatshirts. T-shirts match either capitalization. A t-shirt that also says crew-neck stays under T-shirts. The same buttons filter a chat result, not only the full rack.

**Why it helps.** The rack has 102 pieces. A shopper who wants a hoodie should not have to scroll the whole shop or open the chat. Fewer wrong clicks means they reach a size and a price faster, and the shop spends less time answering "where are the crewnecks?"

## 2. Clearer chat

**What I added.** On a product page, the chat says "Asking about" and the product name, so "this" has a label before the shopper types. When the chat is empty, it offers two starter questions. On the rack those are "What hoodies do you have?" and "What's the cheapest hoodie?" On a product page they are "Do you have this in navy?" and "What sizes are in stock?" Clicking one sends it.

**Why it helps.** A new shopper can see what to ask instead of facing a blank box. On a product page they can see which item the question will be about, so they are less likely to ask "this" and mean a different piece. That saves a wrong answer and a second trip through the chat.

## 3. Lowest price tool

**What I added.** `lowest_price` reads the catalogue and returns the lowest price for a search, plus every piece that shares that price. The prompt tells the assistant to use it for "cheapest" or "least expensive," and to quote that price. The page still draws the card from the catalogue row.

**Why it helps.** Comparing 27 hoodies inside the model is slow, costs more, and can pick the wrong minimum. One database read returns the real low price. Two hoodies are $45, and both come back, so the shop does not advertise one of them as the only deal. The shopper sees the actual cheapest pieces, not a guess.

## 4. Color list tool

**What I added.** `products_in_color` matches the color lists stored on catalogue rows. It does not read the photo or the description. An empty color list does not count as any color. "Navy" matches navy and navy blue. A color with no rows, such as pink, comes back empty, and the assistant is told to say so. The matching pieces are the cards on the page.

**Why it helps.** A shopper asking for navy hoodies, or whether anything is pink, gets an answer tied to the tag colors. The shop does not promise a color it does not list, and it does not hide a piece whose description never used the word. That keeps the rack honest and cuts back-and-forth when a color is sold only on some garments.
