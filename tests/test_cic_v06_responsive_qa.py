import unittest
from integrations.cic_priority_component import priority_cards,QA_CSS
class TestPriorityComponent(unittest.TestCase):
 def test_exact_structure(self):
  s=priority_cards([{'title':'Valoración','controls':'P06, P07','work':'Conciliar deuda y ROIC'}]);self.assertIn('P06, P07',s);self.assertIn('data-role="priority"',s)
 def test_escapes_untrusted_content(self):
  s=priority_cards([{'title':'<script>','controls':'P27','work':'A & B'}]);self.assertIn('&lt;script&gt;',s);self.assertIn('A &amp; B',s)
 def test_missing_field_rejected(self):
  with self.assertRaises(ValueError):priority_cards([{'title':'A','controls':'B'}])
 def test_responsive_css_has_breakpoint(self):
  self.assertIn('@media(max-width:750px)',QA_CSS)
  self.assertIn('flex-direction:column',QA_CSS)
if __name__=='__main__':unittest.main()
