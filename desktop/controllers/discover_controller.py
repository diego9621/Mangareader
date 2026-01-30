from __future__ import annotations
import re
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QListWidgetItem, QMenu
from desktop.widgets.manga_card import MangaCard
from desktop.workers.discover_worker import DiscoverWorker
from desktop.workers.cover_dl_worker import CoverDlWorker
from desktop.utils import pixmap_cover_crop

class DiscoverController:
    def __init__(self, threadpool, discover_list, coverdl_signals, discover_signals, detail_page, open_link_callback):
        self.threadpool = threadpool
        self.discover_list = discover_list
        self.coverdl_signals = coverdl_signals
        self.discover_signals = discover_signals
        self.detail_page = detail_page
        self.open_link_callback = open_link_callback

        self.items_all: list[dict] = []
        self.items_view: list[dict] = []

        self.selected_link: str | None = None

        self.selected_genres: set[str] = set()
        self.render_id = 0
        self.cover_jobs: dict[str, QListWidgetItem] = {}

        self.discover_signals.done.connect(self.on_done)
        self.coverdl_signals.done.connect(self.on_cover_done)

    def load(self, q: str):
        q = (q or "").strip()
        mode = "search" if q else "trending"
        self.discover_list.clear()
        self.discover_list.addItem(QListWidgetItem("Loading…"))
        self.threadpool.start(DiscoverWorker(mode, q, self.discover_signals))

    def on_done(self, items: list, err: str):
        if err:
            self.items_all = []
            self.items_view = []
            self.discover_list.clear()
            self.discover_list.addItem(QListWidgetItem(f"Error: {err}"))
            return
        self.items_all = list(items or [])
        self.apply_filters_and_render()

    def available_genres(self) -> list[str]:
        s: set[str] = set()
        for m in self.items_all:
            for g in (m.get("genres") or []):
                if isinstance(g, str):
                    g = g.strip()
                    if g:
                        s.add(g)
        return sorted(s)

    def populate_genre_menu(self, menu: QMenu):
        menu.clear()
        genres = self.available_genres()
        if not genres:
            a = menu.addAction("No genres")
            a.setEnabled(False)
            return

        a_clear = menu.addAction("Clear")
        a_clear.triggered.connect(lambda: self.set_genres(set()))
        menu.addSeparator()

        selected = set(self.selected_genres)
        for g in genres:
            a = menu.addAction(g)
            a.setCheckable(True)
            a.setChecked(g in selected)
            a.toggled.connect(lambda on, gg=g: self.toggle_genre(gg, on))

    def set_genres(self, genres: set[str]):
        self.selected_genres = set(genres or set())
        self.apply_filters_and_render()

    def toggle_genre(self, genre: str, enabled: bool):
        if enabled:
            self.selected_genres.add(genre)
        else:
            self.selected_genres.discard(genre)
        self.apply_filters_and_render()

    def apply_filters_and_render(self):
        if not self.selected_genres:
            self.items_view = list(self.items_all)
        else:
            want = set(self.selected_genres)
            out = []
            for m in self.items_all:
                gs = set(m.get("genres") or [])
                if gs & want:
                    out.append(m)
            self.items_view = out
        self.render()

    def render(self):
        self.render_id += 1
        rid = self.render_id

        self.discover_list.blockSignals(True)
        self.discover_list.clear()
        self.cover_jobs = {}

        items = self.items_view
        if not items:
            it = QListWidgetItem("No results (genre filter too strict?)")
            self.discover_list.addItem(it)
            self.discover_list.blockSignals(False)
            return

        for i, m in enumerate(items):
            title = self._discover_title(m)
            it = QListWidgetItem()
            it.setData(Qt.UserRole, m)
            it.setSizeHint(QSize(190, 270))

            card = MangaCard(title)
            self.discover_list.addItem(it)
            self.discover_list.setItemWidget(it, card)

            url = (m.get("coverImage") or {}).get("large")
            if url:
                key = f"{rid}:{i}"
                self.cover_jobs[key] = it
                self.threadpool.start(CoverDlWorker(key, url, self.coverdl_signals))

        self.discover_list.blockSignals(False)
        if self.discover_list.count():
            self.discover_list.setCurrentRow(0)

    def on_cover_done(self, key: str, path: str):
        if not path:
            return

        if key.startswith("detail:"):
            try:
                rid = int(key.split(":", 1)[1])
            except:
                return
            if rid != self.render_id:
                return
            pix = pixmap_cover_crop(path, self.detail_page.detail_cover.size())
            if not pix.isNull():
                self.detail_page.detail_cover.setPixmap(pix)
            return

        if ":" not in key:
            return
        rid_s, idx_s = key.split(":", 1)
        try:
            rid = int(rid_s)
            _ = int(idx_s)
        except:
            return
        if rid != self.render_id:
            return

        it = self.cover_jobs.get(key)
        if not it:
            return
        card = self.discover_list.itemWidget(it)
        if not card:
            return
        pix = pixmap_cover_crop(path, QSize(160, 220))
        if not pix.isNull():
            card.set_cover_pixmap(pix)

    def on_selected(self, current: QListWidgetItem | None):
        if not current:
            return
        m = current.data(Qt.UserRole)
        if not m or not isinstance(m, dict):
            return

        rid = self.render_id
        self.detail_page.detail_title.setText(self._discover_title(m))
        self.selected_link = m.get("siteUrl")

        self.detail_page.detail_cover.clear()
        self.detail_page.chapters_preview.clear()
        self.detail_page.detail_sub.setText("")
        self.detail_page.detail_meta.setText("")
        self.detail_page.detail_desc.setText("")
        self.detail_page.set_genres([])

        url = (m.get("coverImage") or {}).get("large")
        if url:
            self.threadpool.start(CoverDlWorker(f"detail:{rid}", url, self.coverdl_signals))

        score = m.get("averageScore")
        status = (m.get("status") or "").replace("_", " ").title()
        fmt = (m.get("format") or "").replace("_", " ").title()
        score_txt = f"{score}%" if score is not None else ""
        self.detail_page.detail_sub.setText(" • ".join(x for x in (fmt, status, score_txt) if x))

        meta_lines = []
        mean = m.get("meanScore")
        if mean is not None:
            meta_lines.append(f"Rating: {mean}%")

        pop = m.get("popularity")
        if pop is not None:
            meta_lines.append(f"Popularity: {pop:,}")

        fav = m.get("favourites")
        if fav is not None:
            meta_lines.append(f"Favourites: {fav:,}")

        chapters = m.get("chapters")
        volumes = m.get("volumes")
        if chapters:
            meta_lines.append(f"Chapters: {chapters}")
        if volumes:
            meta_lines.append(f"Volumes: {volumes}")

        start = self._fmt_date(m.get("startDate") or {})
        end = self._fmt_date(m.get("endDate") or {})
        if start or end:
            meta_lines.append(f"Dates: {start or '?'} → {end or '?'}")

        season = (m.get("season") or "").replace("_", " ").title()
        season_year = m.get("seasonYear")
        if season or season_year:
            s = " ".join(x for x in (season, str(season_year) if season_year else "") if x)
            if s:
                meta_lines.append(s)

        self.detail_page.detail_meta.setText("\n".join(meta_lines))
        self.detail_page.set_genres(m.get("genres") or [])

        desc = self._clean_desc(m.get("description") or "")
        self.detail_page.detail_desc.setText(desc if desc else "No summary available.")

    def open_selected(self, item: QListWidgetItem):
        m = item.data(Qt.UserRole)
        if not m or not isinstance(m, dict):
            return
        url = m.get("siteUrl")
        if url:
            self.open_link_callback(url)

    def open_link(self):
        if self.selected_link:
            self.open_link_callback(self.selected_link)

    def _discover_title(self, m: dict) -> str:
        t = m.get("title") or {}
        return t.get("english") or t.get("romaji") or t.get("native") or "Untitled"

    def _clean_desc(self, s: str) -> str:
        if not s:
            return ""
        s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
        s = re.sub(r"</p\s*>", "\n\n", s, flags=re.I)
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("&mdash;", "—").replace("&quot;", "\"").replace("&amp;", "&")
        s = re.sub(r"\n{3,}", "\n\n", s).strip()
        return s

    def _fmt_date(self, d: dict) -> str:
        if not d:
            return ""
        y = d.get("year")
        m = d.get("month")
        day = d.get("day")
        if not y:
            return ""
        if m and day:
            return f"{y:04d}-{m:02d}-{day:02d}"
        if m:
            return f"{y:04d}-{m:02d}"
        return f"{y:04d}"