import chess
import random

def display_board(board):
    """Display the chess board in a readable format."""
    print(board)
    print()

def get_player_move(board):
    """Prompt the player for a move in UCI format."""
    while True:
        move_input = input("Enter your move (UCI format, e.g. e2e4, g1f3, or 'quit' to exit): ").strip()
        
        if move_input.lower() == 'quit':
            return None
        
        try:
            # Validate if the move is legal
            move = chess.Move.from_uci(move_input)
            if move in board.legal_moves:
                return move
            else:
                print("Illegal move. Please try again.")
        except ValueError:
            print("Invalid move format. Use UCI notation (e.g., e2e4).")

def computer_move(board):
    """Computer selects a random legal move."""
    legal_moves = list(board.legal_moves)
    if legal_moves:
        move = random.choice(legal_moves)
        return move
    return None

def main():
    """Main game loop."""
    board = chess.Board()
    print("Welcome to Python Chess!")
    print("You are playing as White. Enter moves in UCI format (e.g., e2e4, g1f3).")
    print("Type 'quit' to exit.\n")
    
    while not board.is_game_over():
        # Player's turn (White)
        display_board(board)
        print("White to move (you)")
        move = get_player_move(board)
        
        if move is None:
            print("Game aborted.")
            return
        
        board.push(move)
        
        # Check if game ended after player's move
        if board.is_game_over():
            break
        
        # Computer's turn (Black)
        display_board(board)
        print("Black to move (computer)")
        comp_move = computer_move(board)
        if comp_move:
            print(f"Computer plays: {comp_move.uci()}")
            board.push(comp_move)
        else:
            print("Computer has no legal moves.")
    
    # Game over, display result
    display_board(board)
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        print(f"Checkmate! {winner} wins!")
    elif board.is_stalemate():
        print("Stalemate! Draw.")
    elif board.is_insufficient_material():
        print("Draw due to insufficient material.")
    elif board.is_seventyfive_moves():
        print("Draw by 75-move rule.")
    elif board.is_fivefold_repetition():
        print("Draw by fivefold repetition.")
    else:
        print("Game ended.")

if __name__ == "__main__":
    main()