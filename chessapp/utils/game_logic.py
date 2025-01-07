import chess


class ChessEngine:
    PIECE_VALUES = {
        "p": 1,  # Pawn
        "n": 3,  # Knight
        "b": 3,  # Bishop
        "r": 5,  # Rook
        "q": 9,  # Queen
        "k": 0,  # King (not valued directly)
    }

    def __init__(self, match=None):
        if match and match.board_state:
            self.chess_board = chess.Board(match.board_state)
        else:
            self.chess_board = chess.Board()
        self.current_match = match

    def validate_move(self, from_pos, to_pos):
        try:
            proposed_move = chess.Move.from_uci(from_pos + to_pos)
            return proposed_move in self.chess_board.legal_moves
        except ValueError:
            return False

    def execute_move(self, from_pos, to_pos):
        proposed_move = chess.Move.from_uci(from_pos + to_pos)
        if proposed_move in self.chess_board.legal_moves:
            self.chess_board.push(proposed_move)
            if self.current_match:
                self.current_match.board_state = self.chess_board.fen()
                self.current_match.moves_count += 1
                self.current_match.save()
            return True
        return False

    def get_board_position(self):
        position_map = {}
        for square in chess.SQUARES:
            piece = self.chess_board.piece_at(square)
            if piece:
                position_map[chess.SQUARE_NAMES[square]] = self.get_piece_symbol(piece)
        return position_map

    def get_piece_symbol(self, piece):
        symbols = {
            "r": "♜",
            "n": "♞",
            "b": "♝",
            "q": "♛",
            "k": "♚",
            "p": "♟",
            "R": "♖",
            "N": "♘",
            "B": "♗",
            "Q": "♕",
            "K": "♔",
            "P": "♙",
        }
        return symbols.get(piece.symbol())

    def initialize_board(self):
        self.chess_board.reset()
        if self.current_match:
            self.current_match.board_state = self.chess_board.fen()
            self.current_match.save()

    def is_match_over(self):
        return self.chess_board.is_game_over()

    def get_match_result(self):
        return self.chess_board.result()

    def evaluate_board(self):
        """Evaluate the board state from the perspective of the current player."""
        evaluation = 0
        for square in chess.SQUARES:
            piece = self.chess_board.piece_at(square)
            if piece:
                value = self.PIECE_VALUES[piece.symbol().lower()]
                if piece.color == chess.WHITE:
                    evaluation += value
                else:
                    evaluation -= value
        return evaluation

    def minimax(self, depth, is_maximizing, alpha=float("-inf"), beta=float("inf")):
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or self.chess_board.is_game_over():
            return self.evaluate_board()

        if is_maximizing:
            max_eval = float("-inf")
            for move in self.chess_board.legal_moves:
                self.chess_board.push(move)
                eval = self.minimax(depth - 1, False, alpha, beta)
                self.chess_board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in self.chess_board.legal_moves:
                self.chess_board.push(move)
                eval = self.minimax(depth - 1, True, alpha, beta)
                self.chess_board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, depth):
        """Find the best move for the current player."""
        print("true here", True)
        best_move = None
        best_value = float("-inf") if self.chess_board.turn else float("inf")

        for move in self.chess_board.legal_moves:
            self.chess_board.push(move)
            eval = self.minimax(depth - 1, not self.chess_board.turn)
            self.chess_board.pop()

            if self.chess_board.turn:  # Maximizing
                if eval > best_value:
                    best_value = eval
                    best_move = move
            else:  # Minimizing
                if eval < best_value:
                    best_value = eval
                    best_move = move

        return best_move
