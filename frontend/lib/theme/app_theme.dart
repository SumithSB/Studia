import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ── Colour palette ──────────────────────────────────────────────────────────
const kBackground    = Color(0xFF0D0D0D);
const kSurface       = Color(0xFF1A1A1A);
const kCard          = Color(0xFF232323);
const kAccentPurple  = Color(0xFF7C5CFC);
const kAccentBlue    = Color(0xFF5B8FFF);
const kTextPrimary   = Color(0xFFF5F5F5);
const kTextSecondary = Color(0xFF8E8E93);
const kDivider       = Color(0xFF2C2C2E);
const kError         = Color(0xFFFF453A);
const kSuccess       = Color(0xFF30D158);

class AppTheme {
  AppTheme._();

  static ThemeData get dark {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: kBackground,
      colorScheme: const ColorScheme.dark(
        brightness: Brightness.dark,
        primary: kAccentPurple,
        onPrimary: kTextPrimary,
        primaryContainer: Color(0xFF2D1F6E),
        onPrimaryContainer: kAccentPurple,
        secondary: kAccentBlue,
        onSecondary: kTextPrimary,
        surface: kSurface,
        onSurface: kTextPrimary,
        surfaceContainerHighest: kCard,
        onSurfaceVariant: kTextSecondary,
        error: kError,
        outline: kDivider,
      ),
      textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
        bodyColor: kTextPrimary,
        displayColor: kTextPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: kBackground,
        foregroundColor: kTextPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.inter(
          color: kTextPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.3,
        ),
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: kCard,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: kDivider, width: 1),
        ),
        margin: const EdgeInsets.symmetric(vertical: 4),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: kCard,
        hintStyle: const TextStyle(color: kTextSecondary, fontSize: 15),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: kDivider),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: kDivider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: kAccentPurple, width: 1.5),
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: kTextSecondary),
      ),
      dividerTheme: const DividerThemeData(
        color: kDivider,
        thickness: 1,
        space: 1,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: kCard,
        labelStyle: const TextStyle(color: kTextPrimary, fontSize: 13),
        side: const BorderSide(color: kDivider),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        deleteIconColor: kTextSecondary,
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: kAccentPurple,
        linearTrackColor: kCard,
      ),
      listTileTheme: const ListTileThemeData(
        tileColor: Colors.transparent,
        textColor: kTextPrimary,
        iconColor: kTextSecondary,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: kCard,
        contentTextStyle: GoogleFonts.inter(color: kTextPrimary, fontSize: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: kDivider),
        ),
        behavior: SnackBarBehavior.floating,
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          backgroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) return kAccentPurple;
            return kCard;
          }),
          foregroundColor: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) return kTextPrimary;
            return kTextSecondary;
          }),
          side: WidgetStateProperty.all(
            const BorderSide(color: kDivider),
          ),
        ),
      ),
    );
  }
}
