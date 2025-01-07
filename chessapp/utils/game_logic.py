import chess


class ChessEngine:
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
