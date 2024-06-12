import unittest
from agents.query_agent import parse_quiz


llm_response1 = """
Summary: The concept of the relativity of simultaneity is discussed in this text. It explains that simultaneity is relative and can vary depending on the observer's frame of reference. The text also mentions the transformation of space and time coordinates under Lorentz transformation and how events occurring at the same time and same place are considered to have met in space-time.

Quiz:
1. [Question 1 - Basic] What is the relativity of simultaneity?
a) The concept that events can occur at the same time and same place for all observers.
b) The concept that simultaneity is relative and can vary depending on the observer's frame of reference.
c) The concept that time and space coordinates mix with each other under Lorentz transformation.
d) The concept that events occurring at the same time and same place have met in space-time.

2. [Question 2 - Intermediate] How does the relativity of simultaneity affect the perception of simultaneous events in different frames of reference?
a) Simultaneous events will always be perceived as simultaneous in all frames of reference.
b) Simultaneous events may be perceived as non-simultaneous in different frames of reference.
c) Simultaneous events will only be perceived as simultaneous if they occur at the same place.
d) Simultaneous events will only be perceived as simultaneous if they occur at the same time.

3. [Question 3 - Advanced] How does the relativity of simultaneity challenge the notion of absolute time?
a) It suggests that time is absolute and unaffected by the observer's frame of reference.
b) It suggests that time is relative and can vary depending on the observer's frame of reference.
c) It suggests that time can only be measured accurately in a stationary frame of reference.
d) It suggests that time is a social construct and has no objective reality.

Answers:
{
    "1": "b",
    "2": "b",
    "3": "b"
}
"""

llm_response2 = """
Summary: The Effect of Motion on Clocks explains how motion, specifically relative motion, can affect the accuracy of clocks due to the principles of time dilation and the theory of relativity.

Quiz:
- [Question 1 - Basic] How does motion impact the accuracy of clocks?
    a) It speeds up the clocks
    b) It slows down the clocks
    c) It has no effect on the clocks
    d) It stops the clocks

- [Question 2 - Intermediate] How does the theory of relativity play a role in understanding the effect of motion on clocks?
    a) It explains why clocks in motion run faster
    b) It predicts the exact amount of time dilation in moving clocks
    c) It provides a framework for understanding the relationship between motion and time
    d) It has no relevance to the accuracy of clocks

- [Question 3 - Advanced] If a clock is placed on a fast-moving spaceship traveling close to the speed of light, what would be the observed effect on the clock's time compared to a stationary clock on Earth?
    a) The clock on the spaceship would run slower
    b) The clock on the spaceship would run faster
    c) Both clocks would run at the same speed
    d) The clock on the spaceship would stop completely

Answers:
{
    "1": "b",
    "2": "c",
    "3": "a"
}
"""

class TestParseQuiz(unittest.TestCase):
    def setUp(self):
        pass
    def test_parse_quiz1(self):
        result = parse_quiz(llm_response1)
        expected_answers = {"1": "b", "2": "b", "3": "b"}
        self.assertEqual(result['answers'], expected_answers)
        self.assertTrue("What is the relativity of simultaneity?" in result['questions'])

    def test_parse_quiz2(self):
        result = parse_quiz(llm_response2)
        expected_answers = {"1": "b", "2": "c", "3": "a"}
        self.assertEqual(result['answers'], expected_answers)
        self.assertTrue("How does motion impact the accuracy of clocks?" in result['questions'])

if __name__ == '__main__':
    unittest.main()
