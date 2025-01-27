import unittest
import chess
from chessapp.utils.game_logic import (
    ChessEngine,
)  


class TestChessEngine(unittest.TestCase):

    def setUp(self):
        """Set up a new chess engine instance before each test."""
        self.engine = ChessEngine()
        self.board = self.engine.chess_board

    def test_validate_move(self):
        """Test the move validation method."""
        # Valid move example: Move a pawn from e2 to e4
        self.assertTrue(self.engine.validate_move("e2", "e4"))
        # Invalid move example: Move a pawn from e2 to e5
        self.assertFalse(self.engine.validate_move("e2", "e5"))

    def test_execute_move(self):
        """Test the move execution method."""
        # Valid move: Pawn from e2 to e4
        self.assertTrue(self.engine.execute_move("e2", "e4"))
        self.assertEqual(self.board.piece_at(chess.parse_square("e4")).symbol(), "P")

        # Invalid move: Move a pawn from e8 to e5 (which is not valid in the current position)
        self.assertFalse(self.engine.execute_move("e8", "e5"))

    def test_get_board_position(self):
        """Test that the board position is returned correctly."""
        position_map = self.engine.get_board_position()
        self.assertIn("e2", position_map)
        self.assertEqual(position_map["e2"], "♙")  # The initial pawn on e2

    def test_initialize_board(self):
        """Test the board initialization method."""
        self.engine.initialize_board()
        self.assertEqual(
            self.board.fen(), chess.STARTING_FEN
        )  # Ensure it resets to the starting position

    def test_is_match_over(self):
        # Reset the board to the initial state
        self.engine.initialize_board()
        # Execute simple valid moves that result in checkmate (no queen)
        self.engine.execute_move("g2", "g4")
        self.engine.execute_move("e7", "e5") 
        self.engine.execute_move("f2", "f4")  
        self.engine.execute_move(
            "d8", "h4"
        )  

        # Check if game is over (after reaching a theoretical checkmate or stalemate)
        self.assertTrue(self.engine.is_match_over())

    def test_get_match_result(self):
        # Reset the board to the initial state
        self.engine.initialize_board()

        # Set up a checkmate situation
        self.engine.execute_move("g2", "g4")
        self.engine.execute_move("e7", "e5")
        self.engine.execute_move("f2", "f4")
        self.engine.execute_move("d8", "h4")

        # Assert the match result is correctly fetched
        self.assertEqual(self.engine.get_match_result(), "0-1")  # black wins

    def test_evaluate_board(self):
        """Test the evaluation of the board state."""
        evaluation = self.engine.evaluate_board()
        self.assertIsInstance(evaluation, int)

    def test_minimax(self):
        """Test the minimax algorithm for correct functionality."""
        depth = 3
        evaluation = self.engine.minimax(depth, is_maximizing=True)
        self.assertIsInstance(evaluation, int)  # The evaluation should be an integer

    def test_get_best_move(self):
        """Test the get_best_move method."""
        best_move = self.engine.get_best_move(depth=3)
        self.assertIsInstance(
            best_move, chess.Move
        )  # It should return a chess.Move object
        self.assertTrue(best_move in self.board.legal_moves)  # The move must be legal


if __name__ == "__main__":
    unittest.main()
