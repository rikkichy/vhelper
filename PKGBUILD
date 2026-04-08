pkgname=vlauncher
pkgver=0.1.0
pkgrel=1
pkgdesc='Make vtubing suck less on Linux'
arch=('any')
license=('GPL-3.0-or-later')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'protontricks')
source=()

build() {
    true
}

package() {
    cd "$startdir"
    make install DESTDIR="$pkgdir" PREFIX=/usr
}
