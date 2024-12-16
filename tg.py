from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import psycopg2 
TOKEN = "7986810100:AAF-4hKkmVTKqYzyk_DX9ZH6Qz4K1rUSp1M"
DATABASE_URL = "postgresql://postgres:22112005@localhost/exam_platform"


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Сәлем! Бұл Exam Platform бот. Қол жетімді командалар:\n"
        "/student_results <ИИН> - Белгілі студенттің нәтижелерін көру"
    )


async def student_results(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("ИИН енгізіңіз: /student_results <ИИН>")
        return

    iin = context.args[0]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT students.first_name, students.last_name, tests.title, results.score
            FROM results
            JOIN students ON results.student_id = students.id
            JOIN tests ON results.test_id = tests.id
            WHERE students.iin = %s
            ORDER BY results.score DESC;
        """, (iin,))
        results = cursor.fetchall()

        if results:
            response = f"📊 *ИИН {iin} нәтижелері:*\n\n"
            for row in results:
                response += f"📝 {row[2]}: {row[3]} ұпай\n"
        else:
            response = f"Студенттің ИИН {iin} нәтижелері табылған жоқ."

    except Exception as e:
        response = f"Қате: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    await update.message.reply_text(response, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("student_results", student_results))

    print("Бот іске қосылды!")
    app.run_polling()


if __name__ == '__main__':
    main()
