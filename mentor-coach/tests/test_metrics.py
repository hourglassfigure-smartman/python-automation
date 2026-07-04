"""metrics モジュールの単体テスト (API・音声依存なし)。"""

import unittest

from mentor_coach import metrics as m
from mentor_coach.models import Segment


def seg(speaker, start, end, text):
    return Segment(speaker=speaker, start=start, end=end, text=text)


class TestQuestions(unittest.TestCase):
    def test_is_question(self):
        self.assertTrue(m.is_question("どんなことをお話しになりたいですか。"))
        self.assertTrue(m.is_question("それは何ですか？"))
        self.assertTrue(m.is_question("うまくいきそうですか"))
        self.assertFalse(m.is_question("なるほど、そうなんですね。"))
        self.assertFalse(m.is_question(""))

    def test_classify_open_closed(self):
        self.assertEqual(m.classify_question("なぜそう思いますか。"), "open")
        self.assertEqual(m.classify_question("どんな空気ですか。"), "open")
        self.assertEqual(m.classify_question("それでいいですか。"), "closed")

    def test_question_stats_counts_only_coach(self):
        segments = [
            seg("coach", 0, 5, "何が課題ですか。"),
            seg("client", 6, 10, "納期です。これでいいんでしょうか。"),
            seg("coach", 11, 15, "納期なんですね。"),
        ]
        stats = m.question_stats(segments)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["open"], 1)


class TestTiming(unittest.TestCase):
    def test_talk_ratio(self):
        segments = [seg("coach", 0, 10, "a"), seg("client", 10, 40, "b")]
        ratio = m.talk_ratio(segments)
        self.assertAlmostEqual(ratio["coach"], 0.25)
        self.assertAlmostEqual(ratio["client"], 0.75)

    def test_detect_silences(self):
        segments = [seg("coach", 0, 10, "a"), seg("client", 16, 20, "b")]
        silences = m.detect_silences(segments, min_gap=4.0)
        self.assertEqual(len(silences), 1)
        self.assertEqual(silences[0]["duration"], 6.0)
        self.assertEqual(silences[0]["after_speaker"], "coach")
        self.assertEqual(silences[0]["broken_by"], "client")

    def test_no_silence_below_threshold(self):
        segments = [seg("coach", 0, 10, "a"), seg("client", 12, 20, "b")]
        self.assertEqual(m.detect_silences(segments, min_gap=4.0), [])

    def test_detect_interruptions(self):
        segments = [seg("client", 0, 10, "話しています"), seg("coach", 8, 12, "ちょっといいですか")]
        hits = m.detect_interruptions(segments)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["interrupter"], "coach")

    def test_same_speaker_overlap_not_interruption(self):
        segments = [seg("coach", 0, 10, "a"), seg("coach", 9, 12, "b")]
        self.assertEqual(m.detect_interruptions(segments), [])

    def test_speech_rate_shift(self):
        slow = "ゆっくり話す" * 2          # 12文字 / 10秒 = 1.2 cps
        fast = "とても早口で話しています" * 5  # 60文字 / 10秒 = 6.0 cps
        segments = [seg("client", 0, 10, slow), seg("client", 12, 22, fast)]
        shifts = m.speech_rate_shifts(segments, threshold=1.5)
        self.assertEqual(len(shifts), 1)
        self.assertEqual(shifts[0]["direction"], "faster")


class TestTopics(unittest.TestCase):
    def test_similarity_identical_and_disjoint(self):
        self.assertEqual(m._similarity("チームの会議", "チームの会議"), 1.0)
        self.assertEqual(m._similarity("あいうえお", "かきくけこ"), 0.0)

    def test_detect_loops(self):
        # 窓1と窓3が同じ話題(会議)、窓2は別話題(家族)
        a = "会議でメンバーが発言しません。会議の空気が重いです。"
        b = "週末は家族と旅行に行きました。子どもと遊びました。"
        c = "会議でメンバーの発言を増やしたい。会議の空気を変えたい。"
        segments = []
        for i, text in enumerate([a, b, c]):
            for j in range(6):
                t = i * 60 + j * 10
                segments.append(seg("client", t, t + 8, text))
        loops = m.detect_loops(segments, window=6, threshold=0.25)
        self.assertTrue(any(lp["similar_to"] == 0.0 for lp in loops))

    def test_compute_all_keys(self):
        segments = [seg("coach", 0, 5, "何が課題ですか。"), seg("client", 6, 10, "納期です。")]
        result = m.compute_all(segments)
        for key in (
            "talk_ratio", "silences", "speech_rate_shifts", "interruptions",
            "coach_questions", "topic_shifts", "loops",
        ):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
