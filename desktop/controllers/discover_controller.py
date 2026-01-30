from __future__ import annotations
import re
from PySide6.QtCore import Qt, QSize, QUrl, QThreadPool
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from desktop.widgets.manga_card import MangaCard
from desktop.workers.cover_dl_worker import CoverDlWorker, CoverDlSignals
from desktop.workers.discover_worker import DiscoverWorker, DiscoverSignals
from desktop.utils import pixmap_cover_crop


class DiscoverController:
    def __init__(
        self,
        threadpool: QThreadPool,
        discover_list: QListWidget,
        coverdl_signals: CoverDlSignals,
        discover_signals: DiscoverSignals,
        detail_page,
        open_link_callback,
    ):
        self.threadpool = threadpool
        self.discover_list = discover_list
        self.coverdl_signals = coverdl_signals
        self.discover_signals = discover_signals
        self.detail_page = detail_page
        self.open_link_callback = open_link_callback

        self.discover_signals.done.connect(self.on_discover_done)
        self.coverdl_signals.done.connect(self.on_cover_done)

        self.items = []
        self.render_id = 0
        self.cover_jobs: dict[str, QListWidgetItem] = {}
        self.selected_link = None

    def load(self, q: str):
        q = (q or "").strip()
        mode = "search" if q else "trending"
        self.discover_list.clear()
        self.discover_list.addItem(QListWidgetItem("Loading…"))
        self.threadpool.start(DiscoverWorker(mode, q, self.discover_signals))

    def on_discover_done(self, items: list, err: str):
        if err:
            self.discover_list.clear()
            self.discover_list.addItem(QListWidgetItem(f"Error: {err}"))
            return
        self.items = items
        self.render()

    def render(self):
        self.render_id += 1
        rid = self.render_id

        self.discover_list.blockSignals(True)
        self.discover_list.clear()
        self.cover_jobs = {}

        for i, m in enumerate(self.items):
            it = QListWidgetItem()
            it.setData(Qt.UserRole, m)
            it.setSizeHint(QSize(190, 270))
            card = MangaCard(self._title(m))
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
        rid_s, _ = key.split(":", 1)
        try:
            rid = int(rid_s)
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

    def on_selected(self, current):
        if not current:
            return
        m = current.data(Qt.UserRole)
        if not m:
            return

        rid = self.render_id
        self.selected_link = m.get("siteUrl")
        self.detail_page.detail_title.setText(self._title(m))

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

        meta = []
        mean = m.get("meanScore")
        if mean is not None:
            meta.append(f"Rating: {mean}%")
        pop = m.get("popularity")
        if pop is not None:
            meta.append(f"Popularity: {pop:,}")
        fav = m.get("favourites")
        if fav is not None:
            meta.append(f"Favourites: {fav:,}")
        chapters = m.get("chapters")
        volumes = m.get("volumes")
        if chapters:
            meta.append(f"Chapters: {chapters}")
        if volumes:
            meta.append(f"Volumes: {volumes}")

        start = self._fmt_date(m.get("startDate") or {})
        end = self._fmt_date(m.get("endDate") or {})
        if start or end:
            meta.append(f"Dates: {start or '?'} → {end or '?'}")

        season = (m.get("season") or "").replace("_", " ").title()
        season_year = m.get("seasonYear")
        if season or season_year:
            s = " ".join(x for x in (season, str(season_year) if season_year else "") if x)
            if s:
                meta.append(s)

        self.detail_page.detail_meta.setText("\n".join(meta))
        self.detail_page.set_genres(m.get("genres") or [])
        desc = self._clean_desc(m.get("description") or "")
        self.detail_page.detail_desc.setText(desc if desc else "No summary available.")

    def open_selected(self, item: QListWidgetItem):
        m = item.data(Qt.UserRole)
        if not m:
            return
        url = m.get("siteUrl")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def open_link(self):
        if self.selected_link:
            self.open_link_callback(self.selected_link)

    def _title(self, m: dict) -> str:
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