import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <p className="eyebrow">The shop on Broadway</p>
        <h1>Yale gear you can actually wear around campus.</h1>
        <p className="lede">
          Hoodies, crewnecks, and t-shirts. College crests, game-day shirts, and the big Yale lettering people look for when they walk in.
        </p>
        <Link className="button" to="/products">
          Browse products
        </Link>
      </section>

      <section className="band">
        <h2>What is on the rack</h2>
        <div className="cards">
          <article className="card">
            <h3>Hoodies</h3>
            <p>Pullover hoodies count as hoodies here. If it has a hood and you pull it on, it lives in this group.</p>
          </article>
          <article className="card">
            <h3>T-shirts</h3>
            <p>Short-sleeve shirts, whatever way the label capitalizes “t-shirt.” Same thing when you are looking.</p>
          </article>
          <article className="card">
            <h3>The rest</h3>
            <p>Crewnecks, quarter-zips, and jackets. Each one keeps the name it has in the shop.</p>
          </article>
        </div>
      </section>

      <section className="split">
        <div>
          <h2>Price and stock stay honest</h2>
          <p>
            The number on a piece is the price in the shop. If your size is out, we say it is out. We do not guess a color when the tag does not list one.
          </p>
        </div>
        <div>
          <h2>Come by the store</h2>
          <p>57 Broadway, New Haven, CT 06511. The site is for looking through the merch before you ask us what we still have.</p>
        </div>
      </section>
    </>
  )
}
