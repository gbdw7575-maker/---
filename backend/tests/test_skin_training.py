import unittest

from app.classifier.class_definitions import CLASS_PROFILES
from training.prepare_local_skin_dataset import group_id, target_class


def row(final_label, original_class, filename, source="DermNet"):
    return {
        "final_label": final_label,
        "original_class": original_class,
        "filename": filename,
        "source_dataset": source,
    }


class SkinTrainingDataTest(unittest.TestCase):
    def test_expanded_profile_has_fifteen_unique_classes(self):
        codes = [item["short"] for item in CLASS_PROFILES["v3"]]
        self.assertEqual(len(codes), 15)
        self.assertEqual(len(set(codes)), 15)

    def test_keeps_exact_pad_melanoma_and_bcc_labels(self):
        self.assertEqual(target_class(row("Melanoma and Nevi", "MEL", "PAD_PAT_1_2_3.jpg", "PAD")), "MEL")
        self.assertEqual(target_class(row("Basal Cell Carcinoma", "BCC", "PAD_PAT_1_2_4.jpg", "PAD")), "BCC")

    def test_keeps_expanded_exact_labels(self):
        self.assertEqual(target_class(row("Acne and Rosacea", "mixed", "acne.jpg")), "ACNE")
        self.assertEqual(target_class(row("Actinic Keratosis and Malignant Lesions", "ACK", "PAD_PAT_1.jpg", "PAD")), "AK")
        self.assertEqual(target_class(row("Squamous Cell Carcinoma", "SCC", "PAD_PAT_2.jpg", "PAD")), "SCC")
        self.assertEqual(target_class(row("Fungal Infections", "mixed", "tinea.jpg")), "FUNGAL")

    def test_excludes_nevus_from_melanoma(self):
        self.assertIsNone(target_class(row("Melanoma and Nevi", "NEV", "DER_melanocytic-nevi-1.jpg")))
        self.assertEqual(target_class(row("Melanoma and Nevi", "mixed", "DER_malignant-melanoma-1.jpg")), "MEL")

    def test_only_keeps_target_viral_lesions(self):
        self.assertEqual(target_class(row("Viral Infections", "mixed", "DER_molluscum-contagiosum-1.jpg")), "WARTS")
        self.assertIsNone(target_class(row("Viral Infections", "mixed", "DER_herpes-zoster-1.jpg")))

    def test_pad_images_are_grouped_by_patient(self):
        first = row("", "", "PAD_PAT_101_1041_651.jpg", "PAD")
        second = row("", "", "PAD_PAT_101_1041_658.jpg", "PAD")
        self.assertEqual(group_id(first), group_id(second))


if __name__ == "__main__":
    unittest.main()
