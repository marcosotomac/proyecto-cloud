"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  MessageSquare,
  Image as ImageIcon,
  Mic,
  BarChart3,
  Sparkles,
  Zap,
  Shield,
  Rocket,
  ArrowRight,
  Check,
  Stars,
  Brain,
  Cpu,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  // Typing animation state
  const subtitles = [
    "Accede a las mejores herramientas de inteligencia artificial",
    "Genera imágenes increíbles solo con tu imaginación",
    "Conversa con GPT-4 y otros modelos avanzados",
    "Convierte texto a voz en segundos",
    "Analiza tus métricas en tiempo real",
    "Crea contenido asombroso con IA",
  ];

  const [currentSubtitleIndex, setCurrentSubtitleIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [typingSpeed, setTypingSpeed] = useState(100);

  useEffect(() => {
    const currentSubtitle = subtitles[currentSubtitleIndex];

    const handleTyping = () => {
      if (!isDeleting) {
        // Typing
        if (displayedText.length < currentSubtitle.length) {
          setDisplayedText(currentSubtitle.slice(0, displayedText.length + 1));
          setTypingSpeed(50);
        } else {
          // Pause before deleting
          setTimeout(() => setIsDeleting(true), 2000);
        }
      } else {
        // Deleting
        if (displayedText.length > 0) {
          setDisplayedText(currentSubtitle.slice(0, displayedText.length - 1));
          setTypingSpeed(30);
        } else {
          // Move to next subtitle
          setIsDeleting(false);
          setCurrentSubtitleIndex((prev) => (prev + 1) % subtitles.length);
          setTypingSpeed(500);
        }
      }
    };

    const timer = setTimeout(handleTyping, typingSpeed);
    return () => clearTimeout(timer);
  }, [displayedText, isDeleting, currentSubtitleIndex, typingSpeed]);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      router.push("/dashboard/chat");
    } else {
      router.push("/login");
    }
  };

  const features = [
    {
      icon: MessageSquare,
      title: "AI Chat",
      description: "Conversa con modelos de IA de última generación como GPT-4",
      gradient: "from-blue-500 to-cyan-500",
      color: "text-blue-500",
    },
    {
      icon: ImageIcon,
      title: "Generación de Imágenes",
      description: "Crea imágenes increíbles con DALL-E 3 desde texto",
      gradient: "from-purple-500 to-pink-500",
      color: "text-purple-500",
    },
    {
      icon: Mic,
      title: "Text-to-Speech",
      description: "Convierte texto a voz natural en múltiples idiomas",
      gradient: "from-orange-500 to-red-500",
      color: "text-orange-500",
    },
    {
      icon: BarChart3,
      title: "Analytics",
      description: "Rastrea tu uso y métricas en tiempo real",
      gradient: "from-green-500 to-emerald-500",
      color: "text-green-500",
    },
  ];

  const benefits = [
    "Acceso a múltiples modelos de IA",
    "Interfaz intuitiva y moderna",
    "Seguridad y privacidad garantizada",
    "Respuestas en tiempo real",
    "Historial de conversaciones",
    "Descarga de recursos generados",
  ];

  const stats = [
    {
      label: "Usuarios activos",
      value: "10K+",
      icon: Brain,
      color: "text-blue-600",
    },
    { label: "Uptime", value: "99.9%", icon: Shield, color: "text-purple-600" },
    {
      label: "Solicitudes API",
      value: "1M+",
      icon: Cpu,
      color: "text-green-600",
    },
    { label: "Soporte", value: "24/7", icon: Stars, color: "text-orange-600" },
  ];

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring" as const,
        stiffness: 100,
      },
    },
  };

  const floatingVariants = {
    animate: {
      y: [0, -20, 0],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut" as const,
      },
    },
  };

  const scaleVariants = {
    hover: {
      scale: 1.05,
      transition: {
        type: "spring",
        stiffness: 300,
      },
    },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 dark:from-gray-950 dark:via-gray-900 dark:to-gray-800 overflow-hidden">
      {/* Hero Section */}
      <div className="relative min-h-screen flex flex-col">
        {/* Animated Background Orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            className="absolute -top-40 -right-40 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20"
            animate={{
              x: [0, 50, 0],
              y: [0, 30, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
          <motion.div
            className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20"
            animate={{
              x: [0, -30, 0],
              y: [0, -50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
          <motion.div
            className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-3xl opacity-20"
            animate={{
              x: [-40, 40, -40],
              y: [-40, 40, -40],
              scale: [1, 1.15, 1],
            }}
            transition={{
              duration: 12,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        </div>

        {/* Navigation */}
        <motion.nav
          className="relative z-10 container mx-auto px-4 sm:px-6 py-4 sm:py-6"
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 100 }}
        >
          <div className="flex items-center justify-between">
            <motion.div
              className="flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
              </motion.div>
              <span className="text-lg sm:text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
                LLM Platform
              </span>
            </motion.div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <ThemeToggle />
              {isAuthenticated ? (
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button onClick={() => router.push("/dashboard/chat")}>
                    Ir al Dashboard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </motion.div>
              ) : (
                <>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button
                      variant="ghost"
                      onClick={() => router.push("/login")}
                      className="text-sm sm:text-base"
                    >
                      <span className="hidden sm:inline">Iniciar Sesión</span>
                      <span className="sm:hidden">Entrar</span>
                    </Button>
                  </motion.div>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button
                      onClick={() => router.push("/register")}
                      className="text-sm sm:text-base"
                    >
                      <span className="hidden sm:inline">Registrarse</span>
                      <span className="sm:hidden">Registrar</span>
                    </Button>
                  </motion.div>
                </>
              )}
            </div>
          </div>
        </motion.nav>

        {/* Hero Content */}
        <motion.div
          className="relative z-10 container mx-auto px-4 sm:px-6 flex-1 flex items-center justify-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="text-center max-w-4xl mx-auto w-full">
            <motion.div variants={itemVariants}>
              <Badge className="mb-4 text-xs sm:text-sm" variant="secondary">
                <Zap className="h-3 w-3 mr-1" />
                Potenciado por IA
              </Badge>
            </motion.div>

            <motion.h1
              className="text-3xl sm:text-5xl md:text-7xl font-bold mb-4 sm:mb-6 px-4 sm:px-0"
              variants={itemVariants}
            >
              <span className="bg-gradient-to-r from-gray-900 via-purple-900 to-gray-900 dark:from-white dark:via-purple-200 dark:to-white bg-clip-text text-transparent">
                Tu Plataforma de IA
              </span>
              <br />
              <motion.span
                className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
                animate={{
                  backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
                }}
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: "linear",
                }}
              >
                Todo en Uno
              </motion.span>
            </motion.h1>

            <motion.p
              className="text-base sm:text-xl md:text-2xl text-muted-foreground mb-6 sm:mb-8 max-w-2xl mx-auto min-h-[60px] sm:min-h-[80px] flex items-center justify-center px-4 sm:px-0"
              variants={itemVariants}
            >
              <span className="inline-block">
                {displayedText}
                <motion.span
                  className="inline-block w-0.5 h-5 sm:h-6 bg-purple-600 ml-1"
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                />
              </span>
            </motion.p>

            <motion.div
              className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0"
              variants={itemVariants}
            >
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  size="lg"
                  className="text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 w-full sm:w-auto"
                  onClick={handleGetStarted}
                >
                  <Rocket className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                  Comenzar Gratis
                </Button>
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  size="lg"
                  variant="outline"
                  className="text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 w-full sm:w-auto"
                  onClick={() =>
                    document
                      .getElementById("features")
                      ?.scrollIntoView({ behavior: "smooth" })
                  }
                >
                  Conocer Más
                </Button>
              </motion.div>
            </motion.div>

            {/* Floating Icons */}
            <div className="mt-8 sm:mt-16 grid grid-cols-4 gap-4 sm:gap-8 max-w-xl mx-auto px-4 sm:px-0">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  variants={floatingVariants}
                  animate="animate"
                  transition={{ delay: index * 0.2 }}
                  className={`${feature.color}`}
                >
                  <feature.icon className="h-8 w-8 sm:h-12 sm:w-12 mx-auto" />
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Features Section */}
      <motion.div
        id="features"
        className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <motion.div
          className="text-center mb-8 sm:mb-16"
          initial={{ y: 50, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 px-4 sm:px-0">
            Características Potentes
          </h2>
          <p className="text-base sm:text-xl text-muted-foreground max-w-2xl mx-auto px-4 sm:px-0">
            Todo lo que necesitas para aprovechar el poder de la IA
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ y: 50, opacity: 0 }}
              whileInView={{ y: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -10 }}
            >
              <Card className="relative overflow-hidden group h-full">
                <motion.div
                  className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10`}
                  initial={false}
                  animate={{ opacity: 0 }}
                  whileHover={{ opacity: 0.1 }}
                  transition={{ duration: 0.3 }}
                />
                <CardContent className="p-4 sm:p-6 relative z-10">
                  <motion.div
                    className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-3 sm:mb-4 shadow-lg`}
                    whileHover={{ rotate: 360, scale: 1.1 }}
                    transition={{ duration: 0.6 }}
                  >
                    <feature.icon className="h-6 w-6 sm:h-7 sm:w-7 text-white" />
                  </motion.div>
                  <h3 className="text-lg sm:text-xl font-bold mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm sm:text-base text-muted-foreground">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Benefits Section */}
      <motion.div
        className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-12 items-center">
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Badge className="mb-4 text-xs sm:text-sm" variant="secondary">
              <Shield className="h-3 w-3 mr-1" />
              Seguro y Confiable
            </Badge>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6">
              ¿Por qué elegir nuestra plataforma?
            </h2>
            <p className="text-base sm:text-xl text-muted-foreground mb-6 sm:mb-8">
              Diseñada para desarrolladores, creadores y empresas que quieren
              aprovechar el poder de la IA sin complicaciones.
            </p>
            <div className="space-y-4">
              {benefits.map((benefit, index) => (
                <motion.div
                  key={index}
                  className="flex items-center space-x-3"
                  initial={{ x: -20, opacity: 0 }}
                  whileInView={{ x: 0, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ x: 10 }}
                >
                  <motion.div
                    className="flex-shrink-0 w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-green-500 flex items-center justify-center"
                    whileHover={{ scale: 1.2, rotate: 360 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Check className="h-3 w-3 sm:h-4 sm:w-4 text-white" />
                  </motion.div>
                  <span className="text-sm sm:text-lg">{benefit}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="relative"
            initial={{ x: 100, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  className={index % 2 === 1 ? "mt-4 sm:mt-8" : ""}
                  initial={{ scale: 0, opacity: 0 }}
                  whileInView={{ scale: 1, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1, type: "spring" }}
                  whileHover={{ scale: 1.05, rotate: 2 }}
                >
                  <Card className="p-4 sm:p-6 hover:shadow-xl transition-shadow">
                    <motion.div
                      animate={{
                        y: [0, -5, 0],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: index * 0.3,
                      }}
                    >
                      <stat.icon
                        className={`h-6 w-6 sm:h-8 sm:w-8 ${stat.color} mb-2`}
                      />
                    </motion.div>
                    <div className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">
                      <motion.span
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                      >
                        {stat.value}
                      </motion.span>
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground">
                      {stat.label}
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* CTA Section */}
      <motion.div
        className="relative z-10 container mx-auto px-4 sm:px-6 py-12 sm:py-20"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <motion.div
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className="relative overflow-hidden">
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
              animate={{
                backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: "linear",
              }}
              style={{
                backgroundSize: "200% 200%",
                opacity: 0.1,
              }}
            />
            <CardContent className="relative z-10 py-12 sm:py-16 px-4 sm:px-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200 }}
              >
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
                  ¿Listo para empezar?
                </h2>
              </motion.div>
              <motion.p
                className="text-base sm:text-xl text-muted-foreground mb-6 sm:mb-8 max-w-2xl mx-auto"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
              >
                Únete a miles de usuarios que ya están creando con IA
              </motion.p>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  size="lg"
                  className="text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6"
                  onClick={handleGetStarted}
                >
                  <Rocket className="mr-2 h-4 w-4 sm:h-5 sm:w-5" />
                  Comenzar Ahora
                </Button>
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Footer */}
      <motion.footer
        className="relative z-10 border-t"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <motion.div
              className="flex items-center space-x-2 mb-4 md:mb-0"
              whileHover={{ scale: 1.05 }}
            >
              <motion.div
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
              </motion.div>
              <span className="text-sm sm:text-base font-bold">
                LLM Platform
              </span>
            </motion.div>
            <div className="text-xs sm:text-sm text-muted-foreground text-center md:text-left">
              © 2025 LLM Platform. Todos los derechos reservados.
            </div>
          </div>
        </div>
      </motion.footer>
    </div>
  );
}
